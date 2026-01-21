
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
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
    return render(request, 'finance/loan_form.html', {'form': form})
