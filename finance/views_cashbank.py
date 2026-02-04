from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from .models import CashBank
from .forms import CashBankForm


@login_required
def cashbank_list(request):
    """List all cash and bank accounts"""
    cash_accounts = CashBank.objects.filter(account_type='cash').order_by('account_name')
    bank_accounts = CashBank.objects.filter(account_type='bank').order_by('bank_name', 'account_name')
    gold_loan_accounts = CashBank.objects.filter(account_type='gold_loan').order_by('account_name')
    other_investment_accounts = CashBank.objects.filter(account_type='other_investment').order_by('account_name')
    
    total_cash = cash_accounts.aggregate(
        total=Coalesce(Sum('balance'), Decimal('0'))
    )['total']
    
    total_bank = bank_accounts.aggregate(
        total=Coalesce(Sum('balance'), Decimal('0'))
    )['total']

    total_gold_loan = gold_loan_accounts.aggregate(
        total=Coalesce(Sum('balance'), Decimal('0'))
    )['total']

    total_other_investment = other_investment_accounts.aggregate(
        total=Coalesce(Sum('balance'), Decimal('0'))
    )['total']

    total_all = total_cash + total_bank + total_gold_loan + total_other_investment
        'other_investment_accounts': other_investment_accounts,
        'total_cash': total_cash,
        'total_bank': total_bank,
        'total_gold_loan': total_gold_loan,
        'total_other_investment': total_other_investment,
        'total_all': total_all,
    }
    return render(request, 'finance/cashbank_list.html', context)


@login_required
def cashbank_create(request):
    """Create a new cash or bank account"""
    if request.method == 'POST':
        form = CashBankForm(request.POST)
        if form.is_valid():
            cashbank = form.save()
            messages.success(request, f"Account '{cashbank.account_name}' created successfully!")
            return redirect('finance:cashbank_list')
    else:
        form = CashBankForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'finance/cashbank_form.html', context)


@login_required
def cashbank_update(request, pk):
    """Update an existing cash or bank account"""
    cashbank = get_object_or_404(CashBank, pk=pk)
    
    if request.method == 'POST':
        form = CashBankForm(request.POST, instance=cashbank)
        if form.is_valid():
            cashbank = form.save()
            messages.success(request, f"Account '{cashbank.account_name}' updated successfully!")
            return redirect('finance:cashbank_list')
    else:
        form = CashBankForm(instance=cashbank)
    
    context = {'form': form, 'cashbank': cashbank, 'action': 'Update'}
    return render(request, 'finance/cashbank_form.html', context)


@login_required
def cashbank_delete(request, pk):
    """Delete a cash or bank account"""
    cashbank = get_object_or_404(CashBank, pk=pk)
    
    if request.method == 'POST':
        account_name = cashbank.account_name
        cashbank.delete()
        messages.success(request, f"Account '{account_name}' deleted successfully!")
        return redirect('finance:cashbank_list')
    
    context = {'cashbank': cashbank}
    return render(request, 'finance/cashbank_confirm_delete.html', context)


@login_required
def cashbank_toggle_active(request, pk):
    """Toggle active status of an account"""
    cashbank = get_object_or_404(CashBank, pk=pk)
    cashbank.is_active = not cashbank.is_active
    cashbank.save()
    
    status = "activated" if cashbank.is_active else "deactivated"
    messages.success(request, f"Account '{cashbank.account_name}' {status}!")
    return redirect('finance:cashbank_list')
