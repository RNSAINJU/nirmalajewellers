from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.http import JsonResponse
from .models import Expense, Employee, EmployeeSalary, SundryDebtor, DebtorTransaction, SundryCreditor, CreditorTransaction
from .forms import ExpenseForm, EmployeeForm, EmployeeSalaryForm, SundryDebtorForm, DebtorTransactionForm, SundryCreditorForm, CreditorTransactionForm


# EXPENSE VIEWS
@login_required
def expense_list(request):
    expenses = Expense.objects.all()
    category = request.GET.get('category')
    if category:
        expenses = expenses.filter(category=category)
    
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'expenses': expenses,
        'categories': Expense.CATEGORY_CHOICES,
        'total_expenses': total_expenses,
    }
    return render(request, 'finance/expense_list.html', context)


@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('finance:expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'finance/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('finance:expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'finance/expense_form.html', {'form': form, 'title': 'Edit Expense', 'object': expense})


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        return redirect('finance:expense_list')
    return render(request, 'finance/expense_confirm_delete.html', {'object': expense})


# EMPLOYEE VIEWS
@login_required
def employee_list(request):
    employees = Employee.objects.all()
    active_only = request.GET.get('active_only')
    if active_only:
        employees = employees.filter(is_active=True)
    
    context = {
        'employees': employees,
    }
    return render(request, 'finance/employee_list.html', context)


@login_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('finance:employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'finance/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('finance:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'finance/employee_form.html', {'form': form, 'title': 'Edit Employee', 'object': employee})


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('finance:employee_list')
    return render(request, 'finance/employee_confirm_delete.html', {'object': employee})


# EMPLOYEE SALARY VIEWS
@login_required
def salary_list(request):
    salaries = EmployeeSalary.objects.select_related('employee').all()
    employee_id = request.GET.get('employee')
    status = request.GET.get('status')
    
    if employee_id:
        salaries = salaries.filter(employee_id=employee_id)
    if status:
        salaries = salaries.filter(status=status)
    
    total_salary = salaries.aggregate(Sum('total_salary'))['total_salary__sum'] or 0
    total_paid = salaries.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    context = {
        'salaries': salaries,
        'employees': Employee.objects.filter(is_active=True),
        'statuses': EmployeeSalary.STATUS_CHOICES,
        'total_salary': total_salary,
        'total_paid': total_paid,
    }
    return render(request, 'finance/salary_list.html', context)


@login_required
def salary_create(request):
    if request.method == 'POST':
        form = EmployeeSalaryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('finance:salary_list')
    else:
        form = EmployeeSalaryForm()
    return render(request, 'finance/salary_form.html', {'form': form, 'title': 'Add Salary'})


@login_required
def salary_update(request, pk):
    salary = get_object_or_404(EmployeeSalary, pk=pk)
    if request.method == 'POST':
        form = EmployeeSalaryForm(request.POST, instance=salary)
        if form.is_valid():
            form.save()
            return redirect('finance:salary_list')
    else:
        form = EmployeeSalaryForm(instance=salary)
    return render(request, 'finance/salary_form.html', {'form': form, 'title': 'Edit Salary', 'object': salary})


@login_required
def salary_delete(request, pk):
    salary = get_object_or_404(EmployeeSalary, pk=pk)
    if request.method == 'POST':
        salary.delete()
        return redirect('finance:salary_list')
    return render(request, 'finance/salary_confirm_delete.html', {'object': salary})


# SUNDRY DEBTOR VIEWS
@login_required
def debtor_list(request):
    debtors = SundryDebtor.objects.all()
    active_only = request.GET.get('active_only')
    if active_only:
        debtors = debtors.filter(is_active=True)
    
    total_balance = debtors.aggregate(Sum('current_balance'))['current_balance__sum'] or 0
    
    context = {
        'debtors': debtors,
        'total_balance': total_balance,
    }
    return render(request, 'finance/debtor_list.html', context)


@login_required
def debtor_create(request):
    if request.method == 'POST':
        form = SundryDebtorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('finance:debtor_list')
    else:
        form = SundryDebtorForm()
    return render(request, 'finance/debtor_form.html', {'form': form, 'title': 'Add Debtor'})


@login_required
def debtor_update(request, pk):
    debtor = get_object_or_404(SundryDebtor, pk=pk)
    if request.method == 'POST':
        form = SundryDebtorForm(request.POST, instance=debtor)
        if form.is_valid():
            form.save()
            return redirect('finance:debtor_list')
    else:
        form = SundryDebtorForm(instance=debtor)
    return render(request, 'finance/debtor_form.html', {'form': form, 'title': 'Edit Debtor', 'object': debtor})


@login_required
def debtor_delete(request, pk):
    debtor = get_object_or_404(SundryDebtor, pk=pk)
    if request.method == 'POST':
        debtor.delete()
        return redirect('finance:debtor_list')
    return render(request, 'finance/debtor_confirm_delete.html', {'object': debtor})


@login_required
def debtor_detail(request, pk):
    debtor = get_object_or_404(SundryDebtor, pk=pk)
    transactions = debtor.transactions.all()
    
    context = {
        'debtor': debtor,
        'transactions': transactions,
    }
    return render(request, 'finance/debtor_detail.html', context)


@login_required
def debtor_transaction_create(request, debtor_id):
    debtor = get_object_or_404(SundryDebtor, pk=debtor_id)
    if request.method == 'POST':
        form = DebtorTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.debtor = debtor
            transaction.save()
            return redirect('finance:debtor_detail', pk=debtor.pk)
    else:
        form = DebtorTransactionForm(initial={'debtor': debtor})
    return render(request, 'finance/debtor_transaction_form.html', {'form': form, 'debtor': debtor, 'title': 'Add Transaction'})


# SUNDRY CREDITOR VIEWS
@login_required
def creditor_list(request):
    creditors = SundryCreditor.objects.all()
    active_only = request.GET.get('active_only')
    if active_only:
        creditors = creditors.filter(is_active=True)
    
    total_balance = creditors.aggregate(Sum('current_balance'))['current_balance__sum'] or 0
    
    context = {
        'creditors': creditors,
        'total_balance': total_balance,
    }
    return render(request, 'finance/creditor_list.html', context)


@login_required
def creditor_create(request):
    if request.method == 'POST':
        form = SundryCreditorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('finance:creditor_list')
    else:
        form = SundryCreditorForm()
    return render(request, 'finance/creditor_form.html', {'form': form, 'title': 'Add Creditor'})


@login_required
def creditor_update(request, pk):
    creditor = get_object_or_404(SundryCreditor, pk=pk)
    if request.method == 'POST':
        form = SundryCreditorForm(request.POST, instance=creditor)
        if form.is_valid():
            form.save()
            return redirect('finance:creditor_list')
    else:
        form = SundryCreditorForm(instance=creditor)
    return render(request, 'finance/creditor_form.html', {'form': form, 'title': 'Edit Creditor', 'object': creditor})


@login_required
def creditor_delete(request, pk):
    creditor = get_object_or_404(SundryCreditor, pk=pk)
    if request.method == 'POST':
        creditor.delete()
        return redirect('finance:creditor_list')
    return render(request, 'finance/creditor_confirm_delete.html', {'object': creditor})


@login_required
def creditor_detail(request, pk):
    creditor = get_object_or_404(SundryCreditor, pk=pk)
    transactions = creditor.transactions.all()
    
    context = {
        'creditor': creditor,
        'transactions': transactions,
    }
    return render(request, 'finance/creditor_detail.html', context)


@login_required
def creditor_transaction_create(request, creditor_id):
    creditor = get_object_or_404(SundryCreditor, pk=creditor_id)
    if request.method == 'POST':
        form = CreditorTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.creditor = creditor
            transaction.save()
            return redirect('finance:creditor_detail', pk=creditor.pk)
    else:
        form = CreditorTransactionForm(initial={'creditor': creditor})
    return render(request, 'finance/creditor_transaction_form.html', {'form': form, 'creditor': creditor, 'title': 'Add Transaction'})


# API ENDPOINTS
@login_required
def debtors_list_api(request):
    """API endpoint to fetch all debtors for payment selection (both active and inactive)"""
    debtors = SundryDebtor.objects.all().values('id', 'name', 'contact_person', 'phone', 'email', 'current_balance', 'is_active').order_by('name')
    return JsonResponse(list(debtors), safe=False)
