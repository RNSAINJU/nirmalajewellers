
from decimal import Decimal
from io import BytesIO
import openpyxl
from openpyxl import Workbook

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from .models import Loan, LoanInterestPayment, DhukutiLoan, DhukutiKistaPayment, EmiLoan
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


def _compute_dhukuti_summary(received_amount, total_kista, paid_amounts, remaining_base_payment=None, received_kista_number=1):
    """Compute Dhukuti-style payment summary from variable monthly kista amounts."""
    if received_amount <= 0:
        raise ValueError('Received amount must be greater than zero.')
    if total_kista <= 0:
        raise ValueError('Total kista must be greater than zero.')

    paid_rows = []
    total_paid = Decimal('0.00')
    for idx, amount in enumerate(paid_amounts, start=1):
        amt = Decimal(str(amount)).quantize(Decimal('0.01'))
        if amt <= 0:
            continue
        paid_rows.append({'month': idx, 'amount': amt})
        total_paid += amt

    paid_kista = len(paid_rows)
    remaining_kista = max(total_kista - paid_kista, 0)
    raw_diff = received_amount - total_paid
    interest_on_paid_side = raw_diff < 0
    total_interest = abs(raw_diff).quantize(Decimal('0.01'))

    # Interest period starts from the kista where whole amount is received.
    if received_kista_number < 1:
        received_kista_number = 1
    effective_paid_kista = paid_kista - received_kista_number + 1
    elapsed_interest_kista = effective_paid_kista if effective_paid_kista > 0 else 0

    monthly_interest = Decimal('0.00')
    if elapsed_interest_kista > 0:
        monthly_interest = (total_interest / Decimal(str(elapsed_interest_kista))).quantize(Decimal('0.000001'))

    average_interest_rate_percent = Decimal('0.00')
    if received_amount > 0:
        average_interest_rate_percent = ((total_interest / received_amount) * Decimal('100')).quantize(Decimal('0.01'))

    average_monthly_interest_rate_percent = Decimal('0.00')
    if elapsed_interest_kista > 0 and received_amount > 0:
        average_monthly_interest_rate_percent = ((monthly_interest / received_amount) * Decimal('100')).quantize(Decimal('0.01'))

    remaining_interest = (monthly_interest * Decimal(str(remaining_kista))).quantize(Decimal('0.01'))

    if remaining_base_payment is None or remaining_base_payment == Decimal('0'):
        avg_paid = Decimal('0.00')
        if paid_kista > 0:
            avg_paid = (total_paid / Decimal(str(paid_kista))).quantize(Decimal('0.01'))
        remaining_base_payment = (avg_paid * Decimal(str(remaining_kista))).quantize(Decimal('0.01'))
    else:
        remaining_base_payment = Decimal(str(remaining_base_payment)).quantize(Decimal('0.01'))

    to_pay_with_interest_adj = (remaining_base_payment - remaining_interest).quantize(Decimal('0.01'))
    remaining_kista_amount = Decimal('0.00')
    if remaining_kista > 0:
        remaining_kista_amount = (to_pay_with_interest_adj / Decimal(str(remaining_kista))).quantize(Decimal('0.01'))

    return {
        'paid_rows': paid_rows,
        'paid_kista': paid_kista,
        'received_kista_number': received_kista_number,
        'elapsed_interest_kista': elapsed_interest_kista,
        'remaining_kista': remaining_kista,
        'total_paid': total_paid.quantize(Decimal('0.01')),
        'received_amount': received_amount.quantize(Decimal('0.01')),
        'interest_on_paid_side': interest_on_paid_side,
        'total_interest': total_interest,
        'monthly_interest': monthly_interest,
        'average_interest_rate_percent': average_interest_rate_percent,
        'average_monthly_interest_rate_percent': average_monthly_interest_rate_percent,
        'remaining_interest': remaining_interest,
        'remaining_base_payment': remaining_base_payment,
        'to_pay_with_interest_adjustment': to_pay_with_interest_adj,
        'remaining_kista_amount': remaining_kista_amount,
    }


def _compute_emi_schedule(principal, annual_rate, tenure_months):
    """Compute EMI and amortization schedule."""
    if principal <= 0 or annual_rate < 0 or tenure_months <= 0:
        raise ValueError('Principal must be > 0, rate >= 0 and tenure > 0.')

    monthly_rate = annual_rate / Decimal('1200')
    n = int(tenure_months)

    if monthly_rate == 0:
        emi = (principal / Decimal(str(n))).quantize(Decimal('0.01'))
    else:
        factor = (Decimal('1') + monthly_rate) ** n
        emi = (principal * monthly_rate * factor / (factor - Decimal('1'))).quantize(Decimal('0.01'))

    balance = principal.quantize(Decimal('0.01'))
    total_interest = Decimal('0.00')
    total_payment = Decimal('0.00')
    schedule = []

    for month in range(1, n + 1):
        interest_component = (balance * monthly_rate).quantize(Decimal('0.01'))
        principal_component = (emi - interest_component).quantize(Decimal('0.01'))

        if month == n or principal_component > balance:
            principal_component = balance
            installment = (principal_component + interest_component).quantize(Decimal('0.01'))
        else:
            installment = emi

        closing_balance = (balance - principal_component).quantize(Decimal('0.01'))
        if closing_balance < 0:
            closing_balance = Decimal('0.00')

        schedule.append({
            'month': month,
            'opening_balance': balance,
            'installment': installment,
            'interest_component': interest_component,
            'principal_component': principal_component,
            'closing_balance': closing_balance,
        })

        total_interest += interest_component
        total_payment += installment
        balance = closing_balance

    return {
        'emi': emi,
        'total_interest': total_interest.quantize(Decimal('0.01')),
        'total_payment': total_payment.quantize(Decimal('0.01')),
        'schedule': schedule,
    }


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
    if loan.is_settled and loan.interest_payments.exists():
        messages.error(request, 'Cannot add interest payment to a settled loan that already has payment records.')
        return redirect('finance:loan_list')

    # Pre-calculate 3-month (quarterly) interest
    quarterly_interest = loan.quarterly_interest

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            payment_date = request.POST.get('payment_date', '')
            months_covered = Decimal(request.POST.get('months_covered', '3'))
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

    # Determine the from_date for months_covered auto-calculation:
    # use last payment date if exists, else loan start date
    last_payment = loan.interest_payments.order_by('-payment_date', '-created_at').first()
    from_date = str(last_payment.payment_date) if last_payment else str(loan.start_date)

    return render(request, 'finance/loan_interest_payment_form.html', {
        'loan': loan,
        'quarterly_interest': quarterly_interest,
        'monthly_interest': loan.monthly_interest,
        'from_date': from_date,
    })


@login_required
def loan_settle(request, pk):
    """Mark a loan as fully settled/paid"""
    loan = get_object_or_404(Loan, pk=pk)

    if request.method == 'POST':
        settled_date = request.POST.get('settled_date', '')
        final_interest_paid = request.POST.get('final_interest_paid', '')
        settlement_months = request.POST.get('settlement_months', '')

        if not settled_date:
            messages.error(request, 'Settlement date is required.')
            return render(request, 'finance/loan_settle_confirm.html', {'loan': loan})

        try:
            loan.is_settled = True
            loan.settled_date = settled_date
            
            # Update final interest paid if provided
            if final_interest_paid:
                loan.final_interest_paid = Decimal(final_interest_paid)
            
            # Update settlement months if provided
            if settlement_months:
                loan.settlement_months = int(settlement_months)
            
            loan.save()
            
            # Build success message with calculated metrics
            message = f'Loan from {loan.bank_name} (रु{loan.amount}) has been marked as settled.'
            if loan.final_interest_paid:
                message += f' Final interest: रु{loan.final_interest_paid}.'
                if loan.effective_interest_rate:
                    message += f' Effective rate: {loan.effective_interest_rate:.2f}% p.a.'
            
            messages.success(request, message)
            return redirect('finance:loan_list')
        except (ValueError, TypeError) as e:
            messages.error(request, f'Error processing settlement: {str(e)}')
            return render(request, 'finance/loan_settle_confirm.html', {'loan': loan})

    return render(request, 'finance/loan_settle_confirm.html', {'loan': loan})


@login_required
def loan_interest_payment_edit(request, pk):
    """Edit a loan interest payment"""
    payment = get_object_or_404(LoanInterestPayment, pk=pk)
    loan = payment.loan

    if request.method == 'POST':
        try:
            payment.amount = Decimal(request.POST.get('amount', '0'))
            payment.payment_date = request.POST.get('payment_date', '')
            payment.months_covered = Decimal(request.POST.get('months_covered', '3'))
            payment.notes = request.POST.get('notes', '')
            if not payment.payment_date:
                messages.error(request, 'Payment date is required.')
            else:
                payment.save()
                messages.success(request, f'Interest payment updated.')
                return redirect('finance:loan_list')
        except Exception as e:
            messages.error(request, f'Error updating payment: {str(e)}')

    # Determine from_date: use the previous payment date or loan start date
    prev_payment = loan.interest_payments.filter(
        payment_date__lt=payment.payment_date
    ).order_by('-payment_date').first()
    from_date = str(prev_payment.payment_date) if prev_payment else str(loan.start_date)

    return render(request, 'finance/loan_interest_payment_form.html', {
        'loan': loan,
        'quarterly_interest': loan.quarterly_interest,
        'monthly_interest': loan.monthly_interest,
        'from_date': from_date,
        'payment': payment,
    })


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


@login_required
def loan_dhukuti_calculator(request):
    """Finance page to calculate Dhukuti-style payment summary."""
    dhukuti_loans = DhukutiLoan.objects.prefetch_related('paid_kistas').all()
    selected_dhukuti = None
    result = None

    initial = {
        'name': '',
        'received_amount': '',
        'total_kista': '20',
        'received_kista_number': '1',
        'remaining_base_payment': '',
        'paid_amounts_text': '',
        'notes': '',
    }

    selected_dhukuti_id = request.GET.get('dhukuti') or request.POST.get('dhukuti_id')
    if selected_dhukuti_id:
        selected_dhukuti = DhukutiLoan.objects.filter(pk=selected_dhukuti_id).first()
        if selected_dhukuti:
            initial['name'] = selected_dhukuti.name
            initial['received_amount'] = str(selected_dhukuti.received_amount)
            initial['total_kista'] = str(selected_dhukuti.total_kista)
            initial['received_kista_number'] = str(selected_dhukuti.received_kista_number)
            initial['remaining_base_payment'] = str(selected_dhukuti.remaining_base_payment)
            initial['notes'] = selected_dhukuti.notes or ''
            initial['paid_amounts_text'] = '\n'.join(
                str(p.amount) for p in selected_dhukuti.paid_kistas.all().order_by('month_number')
            )
            result = _compute_dhukuti_summary(
                received_amount=selected_dhukuti.received_amount,
                total_kista=selected_dhukuti.total_kista,
                paid_amounts=[p.amount for p in selected_dhukuti.paid_kistas.all().order_by('month_number')],
                remaining_base_payment=selected_dhukuti.remaining_base_payment,
                received_kista_number=selected_dhukuti.received_kista_number,
            )

    if request.method == 'POST':
        initial['name'] = request.POST.get('name', '').strip()
        initial['received_amount'] = request.POST.get('received_amount', '').strip()
        initial['total_kista'] = request.POST.get('total_kista', '').strip()
        initial['received_kista_number'] = request.POST.get('received_kista_number', '').strip()
        initial['remaining_base_payment'] = request.POST.get('remaining_base_payment', '').strip()
        initial['paid_amounts_text'] = request.POST.get('paid_amounts_text', '').strip()
        initial['notes'] = request.POST.get('notes', '').strip()

        try:
            received_amount = Decimal(initial['received_amount'])
            total_kista = int(initial['total_kista'])
            received_kista_number = int(initial['received_kista_number'] or '1')

            paid_amounts = []
            for line in initial['paid_amounts_text'].splitlines():
                normalized = line.replace(',', '').strip()
                if not normalized:
                    continue
                paid_amounts.append(Decimal(normalized))

            remaining_base_payment = None
            if initial['remaining_base_payment']:
                remaining_base_payment = Decimal(initial['remaining_base_payment'])

            result = _compute_dhukuti_summary(
                received_amount=received_amount,
                total_kista=total_kista,
                paid_amounts=paid_amounts,
                remaining_base_payment=remaining_base_payment,
                received_kista_number=received_kista_number,
            )

            record_name = initial['name'] or f"Dhukuti Loan {received_amount}"

            if request.POST.get('update_record') == '1':
                if not selected_dhukuti:
                    messages.error(request, 'No Dhukuti record selected to update. Please load a saved record first.')
                else:
                    selected_dhukuti.name = record_name
                    selected_dhukuti.received_amount = received_amount
                    selected_dhukuti.total_kista = total_kista
                    selected_dhukuti.received_kista_number = received_kista_number
                    selected_dhukuti.remaining_base_payment = result['remaining_base_payment']
                    selected_dhukuti.notes = initial['notes']
                    selected_dhukuti.save()

                    # Replace existing paid-kista rows with updated values from form.
                    selected_dhukuti.paid_kistas.all().delete()
                    for row in result['paid_rows']:
                        DhukutiKistaPayment.objects.create(
                            loan=selected_dhukuti,
                            month_number=row['month'],
                            amount=row['amount'],
                        )

                    messages.success(request, f'Dhukuti loan record "{selected_dhukuti.name}" updated successfully.')
                    dhukuti_loans = DhukutiLoan.objects.prefetch_related('paid_kistas').all()

            elif request.POST.get('save_record') == '1':
                dhukuti_loan = DhukutiLoan.objects.create(
                    name=record_name,
                    received_amount=received_amount,
                    total_kista=total_kista,
                    received_kista_number=received_kista_number,
                    remaining_base_payment=result['remaining_base_payment'],
                    notes=initial['notes'],
                )
                for row in result['paid_rows']:
                    DhukutiKistaPayment.objects.create(
                        loan=dhukuti_loan,
                        month_number=row['month'],
                        amount=row['amount'],
                    )

                messages.success(request, f'Dhukuti loan record "{dhukuti_loan.name}" saved successfully.')
                selected_dhukuti = dhukuti_loan
                dhukuti_loans = DhukutiLoan.objects.prefetch_related('paid_kistas').all()
        except Exception as exc:
            messages.error(request, f'Unable to calculate Dhukuti payment: {exc}')

    context = {
        'title': 'Dhukuti Loans',
        'page_title': 'Dhukuti Loans',
        'dhukuti_loans': dhukuti_loans,
        'selected_dhukuti': selected_dhukuti,
        'initial': initial,
        'result': result,
    }
    return render(request, 'finance/loan_emi_calculator.html', context)


@login_required
def loan_dhukuti_delete(request, pk):
    """Delete a saved Dhukuti loan record and its kista rows."""
    dhukuti_loan = get_object_or_404(DhukutiLoan, pk=pk)
    if request.method == 'POST':
        loan_name = dhukuti_loan.name
        dhukuti_loan.delete()
        messages.success(request, f'Dhukuti loan record "{loan_name}" deleted successfully.')
    return redirect('finance:loan_dhukuti_calculator')


@login_required
def loan_emi_calculator(request):
    """Separate EMI loans calculator and record manager."""
    emi_loans = EmiLoan.objects.all()
    selected_emi = None
    result = None

    initial = {
        'name': '',
        'principal': '',
        'current_principal': '',
        'annual_interest_rate': '',
        'tenure_months': '12',
        'notes': '',
    }

    selected_emi_id = request.GET.get('emi') or request.POST.get('emi_id')
    if selected_emi_id:
        selected_emi = EmiLoan.objects.filter(pk=selected_emi_id).first()
        if selected_emi:
            initial['name'] = selected_emi.name
            initial['principal'] = str(selected_emi.principal)
            initial['current_principal'] = str(selected_emi.current_principal) if selected_emi.current_principal else ''
            initial['annual_interest_rate'] = str(selected_emi.annual_interest_rate)
            initial['tenure_months'] = str(selected_emi.tenure_months)
            initial['notes'] = selected_emi.notes or ''

            principal_for_calc = selected_emi.current_principal if selected_emi.current_principal else selected_emi.principal
            result = _compute_emi_schedule(
                principal=principal_for_calc,
                annual_rate=selected_emi.annual_interest_rate,
                tenure_months=selected_emi.tenure_months,
            )
            result['calculation_principal'] = principal_for_calc

    if request.method == 'POST':
        initial['name'] = request.POST.get('name', '').strip()
        initial['principal'] = request.POST.get('principal', '').strip()
        initial['current_principal'] = request.POST.get('current_principal', '').strip()
        initial['annual_interest_rate'] = request.POST.get('annual_interest_rate', '').strip()
        initial['tenure_months'] = request.POST.get('tenure_months', '').strip()
        initial['notes'] = request.POST.get('notes', '').strip()

        try:
            principal = Decimal(initial['principal'])
            current_principal = Decimal(initial['current_principal']) if initial['current_principal'] else None
            annual_rate = Decimal(initial['annual_interest_rate'])
            tenure_months = int(initial['tenure_months'])

            principal_for_calc = current_principal if current_principal else principal

            result = _compute_emi_schedule(
                principal=principal_for_calc,
                annual_rate=annual_rate,
                tenure_months=tenure_months,
            )
            result['calculation_principal'] = principal_for_calc

            record_name = initial['name'] or f"EMI Loan {principal}"
            if request.POST.get('update_record') == '1':
                if not selected_emi:
                    messages.error(request, 'No EMI record selected to update. Please load a saved record first.')
                else:
                    selected_emi.name = record_name
                    selected_emi.principal = principal
                    selected_emi.current_principal = current_principal
                    selected_emi.annual_interest_rate = annual_rate
                    selected_emi.tenure_months = tenure_months
                    selected_emi.notes = initial['notes']
                    selected_emi.save()
                    messages.success(request, f'EMI loan record "{selected_emi.name}" updated successfully.')
                    emi_loans = EmiLoan.objects.all()
            elif request.POST.get('save_record') == '1':
                selected_emi = EmiLoan.objects.create(
                    name=record_name,
                    principal=principal,
                    current_principal=current_principal,
                    annual_interest_rate=annual_rate,
                    tenure_months=tenure_months,
                    notes=initial['notes'],
                )
                messages.success(request, f'EMI loan record "{selected_emi.name}" saved successfully.')
                emi_loans = EmiLoan.objects.all()
        except Exception as exc:
            messages.error(request, f'Unable to calculate EMI: {exc}')

    context = {
        'title': 'EMI Loans',
        'page_title': 'EMI Loans',
        'emi_loans': emi_loans,
        'selected_emi': selected_emi,
        'initial': initial,
        'result': result,
    }
    return render(request, 'finance/loan_emi_separate.html', context)


@login_required
def loan_emi_delete(request, pk):
    """Delete a saved EMI loan record."""
    emi_loan = get_object_or_404(EmiLoan, pk=pk)
    if request.method == 'POST':
        loan_name = emi_loan.name
        emi_loan.delete()
        messages.success(request, f'EMI loan record "{loan_name}" deleted successfully.')
    return redirect('finance:loan_emi_calculator')
