
from decimal import Decimal
from io import BytesIO
import openpyxl
from openpyxl import Workbook

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from .models import Loan, LoanInterestPayment
from .forms import LoanForm


def _safe_decimal(val):
    try:
        return Decimal(str(val)) if val not in (None, '') else Decimal('0')
    except Exception:
        return Decimal('0')


def _extract_date(val):
    """Extract date in YYYY-MM-DD format from various input types."""
    if not val:
        return None
    try:
        # Convert to string and extract only date part (YYYY-MM-DD)
        date_str = str(val)
        # If it has time component, split it
        if ' ' in date_str:
            date_str = date_str.split(' ')[0]
        return date_str
    except Exception:
        return None


@login_required
def loan_list(request):
    status_filter = request.GET.get('status', 'active')
    all_loans = Loan.objects.all().order_by('-start_date', '-created_at')

    if status_filter == 'settled':
        loans = all_loans.filter(is_settled=True)
    elif status_filter == 'all':
        loans = all_loans
    else:
        loans = all_loans.filter(is_settled=False)

    # Calculate total loan amount for shown loans
    total_loan_amount = loans.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')

    # Calculate tentative interest totals for active loans only
    active_loans = all_loans.filter(is_settled=False)
    total_monthly_interest = Decimal('0')
    total_quarterly_interest = Decimal('0')
    total_yearly_interest = Decimal('0')
    for loan in active_loans:
        total_monthly_interest += loan.monthly_interest
        total_quarterly_interest += loan.quarterly_interest
        total_yearly_interest += loan.yearly_interest

    # Calculate bank-wise totals for shown loans
    bank_totals = {}
    for loan in loans:
        bank_name = loan.bank_name
        if bank_name not in bank_totals:
            bank_totals[bank_name] = {
                'total_amount': Decimal('0'),
                'loan_count': 0
            }
        bank_totals[bank_name]['total_amount'] += loan.amount
        bank_totals[bank_name]['loan_count'] += 1

    # Sort banks by amount (descending)
    sorted_banks = sorted(bank_totals.items(), key=lambda x: x[1]['total_amount'], reverse=True)

    # Stats
    active_count = active_loans.count()
    settled_count = all_loans.filter(is_settled=True).count()

    context = {
        'loans': loans,
        'total_loan_amount': total_loan_amount,
        'total_monthly_interest': total_monthly_interest,
        'total_quarterly_interest': total_quarterly_interest,
        'total_yearly_interest': total_yearly_interest,
        'bank_totals': sorted_banks,
        'status_filter': status_filter,
        'active_count': active_count,
        'settled_count': settled_count,
    }
    return render(request, 'finance/loan_list.html', context)


@login_required
def loan_create(request):
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loan added successfully!')
            return redirect('finance:loan_list')
    else:
        form = LoanForm()
    return render(request, 'finance/loan_form.html', {'form': form, 'title': 'Add Loan'})


@login_required
def loan_update(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    if request.method == 'POST':
        form = LoanForm(request.POST, instance=loan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loan updated successfully!')
            return redirect('finance:loan_list')
    else:
        form = LoanForm(instance=loan)
    return render(request, 'finance/loan_form.html', {'form': form, 'title': 'Edit Loan', 'object': loan})


@login_required
def loan_delete(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    if request.method == 'POST':
        loan.delete()
        messages.success(request, 'Loan deleted successfully!')
        return redirect('finance:loan_list')
    return render(request, 'finance/loan_confirm_delete.html', {'object': loan})


@login_required
def loan_export(request):
    """Export all loans to XLSX file"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Loans"
    
    ws.append(["bank_name", "amount", "interest_rate", "start_date", "notes"])
    for loan in Loan.objects.all().order_by('-start_date', '-created_at'):
        ws.append([
            loan.bank_name,
            float(loan.amount),
            float(loan.interest_rate),
            str(loan.start_date) if loan.start_date else '',
            loan.notes or '',
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="loans.xlsx"'
    return response


@login_required
def loan_import(request):
    """Import loans from XLSX file"""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            created = 0
            updated = 0
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                
                bank_name, amount, interest_rate, start_date, notes = row[:5]
                
                # Skip if bank name is empty
                if not bank_name:
                    continue
                
                start_date = _extract_date(start_date)
                if not start_date:
                    continue
                
                loan, created_flag = Loan.objects.update_or_create(
                    bank_name=bank_name,
                    start_date=start_date,
                    defaults={
                        'amount': _safe_decimal(amount),
                        'interest_rate': _safe_decimal(interest_rate),
                        'notes': notes or '',
                    }
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1
            
            messages.success(request, f'Imported {created} new loans, updated {updated} existing loans')
        except Exception as e:
            messages.error(request, f'Import failed: {str(e)}')
    
    return redirect('finance:loan_list')


@login_required
def loan_add_interest(request, pk):
    """Add a 3-month interest payment for a loan"""
    loan = get_object_or_404(Loan, pk=pk)
    if loan.is_settled:
        messages.error(request, 'Cannot add interest payment to a settled loan.')
        return redirect('finance:loan_list')

    # Pre-calculate 3-month (quarterly) interest
    quarterly_interest = loan.quarterly_interest

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            payment_date = request.POST.get('payment_date', '')
            months_covered = int(request.POST.get('months_covered', 3))
            notes = request.POST.get('notes', '')

            if not payment_date:
                messages.error(request, 'Payment date is required.')
                return render(request, 'finance/loan_interest_payment_form.html', {
                    'loan': loan,
                    'quarterly_interest': quarterly_interest,
                    'monthly_interest': loan.monthly_interest,
                })

            LoanInterestPayment.objects.create(
                loan=loan,
                amount=amount,
                payment_date=payment_date,
                months_covered=months_covered,
                notes=notes,
            )
            messages.success(request, f'Interest payment of रु{amount} recorded for {loan.bank_name} ({months_covered} months).')
            return redirect('finance:loan_list')
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')

    return render(request, 'finance/loan_interest_payment_form.html', {
        'loan': loan,
        'quarterly_interest': quarterly_interest,
        'monthly_interest': loan.monthly_interest,
    })


@login_required
def loan_settle(request, pk):
    """Mark a loan as fully settled/paid"""
    loan = get_object_or_404(Loan, pk=pk)

    if request.method == 'POST':
        settled_date = request.POST.get('settled_date', '')
        if not settled_date:
            messages.error(request, 'Settled date is required.')
            return render(request, 'finance/loan_settle_confirm.html', {'loan': loan})

        loan.is_settled = True
        loan.settled_date = settled_date
        loan.save()
        messages.success(request, f'Loan from {loan.bank_name} (रु{loan.amount}) has been marked as settled.')
        return redirect('finance:loan_list')

    return render(request, 'finance/loan_settle_confirm.html', {'loan': loan})


@login_required
def loan_interest_payment_delete(request, pk):
    """Delete a loan interest payment"""
    payment = get_object_or_404(LoanInterestPayment, pk=pk)
    if request.method == 'POST':
        loan_pk = payment.loan.pk
        payment.delete()
        messages.success(request, 'Interest payment deleted.')
        return redirect('finance:loan_list')
    return render(request, 'finance/loan_interest_payment_confirm_delete.html', {'payment': payment})
