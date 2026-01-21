
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Loan
from .forms import LoanForm


@login_required
def loan_list(request):
    loans = Loan.objects.all().order_by('-start_date', '-created_at')
    return render(request, 'finance/loan_list.html', {'loans': loans})


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
