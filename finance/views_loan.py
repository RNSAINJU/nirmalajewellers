
from decimal import Decimal
from io import BytesIO
import openpyxl
from openpyxl import Workbook

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from .models import Loan
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
    loans = Loan.objects.all().order_by('-start_date', '-created_at')
    
    # Calculate total loan amount
    total_loan_amount = loans.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    # Calculate total monthly interest amount
    # Formula: (Loan Amount * Interest Rate) / 100 / 12 for each loan
    total_monthly_interest = Decimal('0')
    for loan in loans:
        monthly_interest = (loan.amount * loan.interest_rate) / 100 / 12
        total_monthly_interest += monthly_interest
    
    context = {
        'loans': loans,
        'total_loan_amount': total_loan_amount,
        'total_monthly_interest': total_monthly_interest,
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

