from decimal import Decimal
from io import BytesIO
import openpyxl
from openpyxl import Workbook

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import ExpenseForm, EmployeeForm, EmployeeSalaryForm, SundryDebtorForm, DebtorTransactionForm, SundryCreditorForm, CreditorTransactionForm
from .models import Expense, Employee, EmployeeSalary, SundryDebtor, DebtorTransaction, SundryCreditor, CreditorTransaction


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


# IMPORT/EXPORT HELPERS
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


# EXPENSE IMPORT/EXPORT
@login_required
def expense_export(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Expenses"
    
    ws.append(["category", "description", "amount", "expense_date", "notes"])
    for e in Expense.objects.all().order_by('-expense_date'):
        ws.append([
            e.category,
            e.description,
            float(e.amount),
            str(e.expense_date) if e.expense_date else '',
            e.notes or "",
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="expenses.xlsx"'
    return response


@login_required
def expense_import(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            created = 0
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                category, description, amount, expense_date, notes = row[:5]
                expense_date = _extract_date(expense_date)
                if not expense_date:
                    continue
                
                Expense.objects.create(
                    category=category or 'other',
                    description=description or '',
                    amount=_safe_decimal(amount),
                    expense_date=expense_date,
                    notes=notes or '',
                )
                created += 1
            messages.success(request, f"Imported {created} expenses")
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
    return redirect('finance:expense_list')


# EMPLOYEE IMPORT/EXPORT
@login_required
def employee_export(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Employees"
    
    ws.append(["first_name", "last_name", "email", "phone", "position", "base_salary", "hire_date", "is_active"])
    for emp in Employee.objects.all().order_by('first_name', 'last_name'):
        ws.append([
            emp.first_name,
            emp.last_name,
            emp.email or '',
            emp.phone or '',
            emp.position,
            float(emp.base_salary),
            str(emp.hire_date) if emp.hire_date else '',
            'true' if emp.is_active else 'false',
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="employees.xlsx"'
    return response


@login_required
def employee_import(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            created = 0
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                first_name, last_name, email, phone, position, base_salary, hire_date, is_active = row[:8]
                
                is_active_bool = str(is_active).lower() in ['1', 'true', 'yes', 'y']
                emp, _created = Employee.objects.update_or_create(
                    email=email or None,
                    defaults={
                        'first_name': first_name or '',
                        'last_name': last_name or '',
                        'phone': phone or '',
                        'position': position or '',
                        'base_salary': _safe_decimal(base_salary),
                        'hire_date': _extract_date(hire_date),
                        'is_active': is_active_bool,
                    }
                )
                if _created:
                    created += 1
            messages.success(request, f"Imported {created} employees (existing emails updated)")
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
    return redirect('finance:employee_list')


# SALARY IMPORT/EXPORT
@login_required
def salary_export(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Salaries"
    
    ws.append([
        "employee_email", "employee_name", "month", "base_salary", "bonus", "deductions",
        "total_salary", "amount_paid", "status", "paid_date", "notes"
    ])
    for s in EmployeeSalary.objects.select_related('employee').all().order_by('-month'):
        ws.append([
            s.employee.email or '',
            f"{s.employee.first_name} {s.employee.last_name}",
            str(s.month) if s.month else '',
            float(s.base_salary),
            float(s.bonus),
            float(s.deductions),
            float(s.total_salary),
            float(s.amount_paid),
            s.status,
            str(s.paid_date) if s.paid_date else '',
            s.notes or '',
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="salaries.xlsx"'
    return response


@login_required
def salary_import(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            created = 0
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                employee_email, employee_name, month, base_salary, bonus, deductions, total_salary, amount_paid, status, paid_date, notes = row[:11]
                
                try:
                    employee = Employee.objects.get(email=employee_email)
                except Employee.DoesNotExist:
                    continue

                month = _extract_date(month)
                if not month:
                    continue

                _, created_flag = EmployeeSalary.objects.update_or_create(
                    employee=employee,
                    month=month,
                    defaults={
                        'base_salary': _safe_decimal(base_salary),
                        'bonus': _safe_decimal(bonus),
                        'deductions': _safe_decimal(deductions),
                        'amount_paid': _safe_decimal(amount_paid),
                        'status': status or 'pending',
                        'paid_date': _extract_date(paid_date),
                        'notes': notes or '',
                    }
                )
                if created_flag:
                    created += 1
            messages.success(request, f"Imported {created} salary rows (matched by employee email + month)")
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
    return redirect('finance:salary_list')


# DEBTOR IMPORT/EXPORT
@login_required
def debtor_export(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Debtors"
    
    ws.append(["name", "contact_person", "phone", "email", "address", "opening_balance", "current_balance", "credit_limit", "is_active", "notes"])
    for d in SundryDebtor.objects.all().order_by('name'):
        ws.append([
            d.name,
            d.contact_person or '',
            d.phone or '',
            d.email or '',
            d.address or '',
            float(d.opening_balance),
            float(d.current_balance),
            float(d.credit_limit),
            'true' if d.is_active else 'false',
            d.notes or '',
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="debtors.xlsx"'
    return response


@login_required
def debtor_import(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            created = 0
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                name, contact_person, phone, email, address, opening_balance, current_balance, credit_limit, is_active, notes = row[:10]
                
                is_active_bool = str(is_active).lower() in ['1', 'true', 'yes', 'y']
                debtor, created_flag = SundryDebtor.objects.update_or_create(
                    name=name or '',
                    defaults={
                        'contact_person': contact_person or '',
                        'phone': phone or '',
                        'email': email or '',
                        'address': address or '',
                        'opening_balance': _safe_decimal(opening_balance),
                        'current_balance': _safe_decimal(current_balance),
                        'credit_limit': _safe_decimal(credit_limit),
                        'is_active': is_active_bool,
                        'notes': notes or '',
                    }
                )
                if created_flag:
                    created += 1
            messages.success(request, f"Imported {created} debtors (matching by name)")
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
    return redirect('finance:debtor_list')


# CREDITOR IMPORT/EXPORT
@login_required
def creditor_export(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Creditors"
    
    ws.append(["name", "contact_person", "phone", "email", "address", "opening_balance", "current_balance", "is_active", "notes"])
    for c in SundryCreditor.objects.all().order_by('name'):
        ws.append([
            c.name,
            c.contact_person or '',
            c.phone or '',
            c.email or '',
            c.address or '',
            float(c.opening_balance),
            float(c.current_balance),
            'true' if c.is_active else 'false',
            c.notes or '',
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="creditors.xlsx"'
    return response


@login_required
def creditor_import(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            created = 0
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                name, contact_person, phone, email, address, opening_balance, current_balance, is_active, notes = row[:9]
                
                is_active_bool = str(is_active).lower() in ['1', 'true', 'yes', 'y']
                _, created_flag = SundryCreditor.objects.update_or_create(
                    name=name or '',
                    defaults={
                        'contact_person': contact_person or '',
                        'phone': phone or '',
                        'email': email or '',
                        'address': address or '',
                        'opening_balance': _safe_decimal(opening_balance),
                        'current_balance': _safe_decimal(current_balance),
                        'is_active': is_active_bool,
                        'notes': notes or '',
                    }
                )
                if created_flag:
                    created += 1
            messages.success(request, f"Imported {created} creditors (matching by name)")
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
    return redirect('finance:creditor_list')


# BULK FINANCE EXPORT (Single XLSX with multiple sheets)
@login_required
def finance_export_all(request):
    """Export all finance data as a single Excel file with multiple sheets."""
    wb = Workbook()
    # Remove default sheet
    if wb.active:
        wb.remove(wb.active)
    
    # Expenses Sheet
    ws_expenses = wb.create_sheet("Expenses")
    ws_expenses.append(["category", "description", "amount", "expense_date", "notes"])
    for e in Expense.objects.all().order_by('-expense_date'):
        ws_expenses.append([
            e.category,
            e.description,
            float(e.amount),
            str(e.expense_date) if e.expense_date else '',
            e.notes or "",
        ])
    
    # Employees Sheet
    ws_employees = wb.create_sheet("Employees")
    ws_employees.append(["first_name", "last_name", "email", "phone", "position", "base_salary", "hire_date", "is_active"])
    for emp in Employee.objects.all().order_by('first_name', 'last_name'):
        ws_employees.append([
            emp.first_name,
            emp.last_name,
            emp.email or '',
            emp.phone or '',
            emp.position,
            float(emp.base_salary),
            str(emp.hire_date) if emp.hire_date else '',
            'true' if emp.is_active else 'false',
        ])
    
    # Salaries Sheet
    ws_salaries = wb.create_sheet("Salaries")
    ws_salaries.append([
        "employee_email", "employee_name", "month", "base_salary", "bonus", "deductions",
        "total_salary", "amount_paid", "status", "paid_date", "notes"
    ])
    for s in EmployeeSalary.objects.select_related('employee').all().order_by('-month'):
        ws_salaries.append([
            s.employee.email or '',
            f"{s.employee.first_name} {s.employee.last_name}",
            str(s.month) if s.month else '',
            float(s.base_salary),
            float(s.bonus),
            float(s.deductions),
            float(s.total_salary),
            float(s.amount_paid),
            s.status,
            str(s.paid_date) if s.paid_date else '',
            s.notes or '',
        ])
    
    # Debtors Sheet
    ws_debtors = wb.create_sheet("Debtors")
    ws_debtors.append(["name", "contact_person", "phone", "email", "address", "opening_balance", "current_balance", "credit_limit", "is_active", "notes"])
    for d in SundryDebtor.objects.all().order_by('name'):
        ws_debtors.append([
            d.name,
            d.contact_person or '',
            d.phone or '',
            d.email or '',
            d.address or '',
            float(d.opening_balance),
            float(d.current_balance),
            float(d.credit_limit),
            'true' if d.is_active else 'false',
            d.notes or '',
        ])
    
    # Creditors Sheet
    ws_creditors = wb.create_sheet("Creditors")
    ws_creditors.append(["name", "contact_person", "phone", "email", "address", "opening_balance", "current_balance", "is_active", "notes"])
    for c in SundryCreditor.objects.all().order_by('name'):
        ws_creditors.append([
            c.name,
            c.contact_person or '',
            c.phone or '',
            c.email or '',
            c.address or '',
            float(c.opening_balance),
            float(c.current_balance),
            'true' if c.is_active else 'false',
            c.notes or '',
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=\"finance_data.xlsx\"'
    return response


# BULK FINANCE IMPORT (Single XLSX with multiple sheets)
@login_required
def finance_import_all(request):
    """Import all finance data from a single Excel file with multiple sheets."""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        stats = {'expenses': 0, 'employees': 0, 'salaries': 0, 'debtors': 0, 'creditors': 0}
        
        try:
            wb = openpyxl.load_workbook(file)
            
            # Import Expenses
            if 'Expenses' in wb.sheetnames:
                ws = wb['Expenses']
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if not any(row):
                        continue
                    category, description, amount, expense_date, notes = row[:5]
                    expense_date = _extract_date(expense_date)
                    if expense_date:
                        Expense.objects.create(
                            category=category or 'other',
                            description=description or '',
                            amount=_safe_decimal(amount),
                            expense_date=expense_date,
                            notes=notes or '',
                        )
                        stats['expenses'] += 1
            
            # Import Employees
            if 'Employees' in wb.sheetnames:
                ws = wb['Employees']
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if not any(row):
                        continue
                    first_name, last_name, email, phone, position, base_salary, hire_date, is_active = row[:8]
                    is_active_bool = str(is_active).lower() in ['1', 'true', 'yes', 'y']
                    emp, created = Employee.objects.update_or_create(
                        email=email or None,
                        defaults={
                            'first_name': first_name or '',
                            'last_name': last_name or '',
                            'phone': phone or '',
                            'position': position or '',
                            'base_salary': _safe_decimal(base_salary),
                            'hire_date': _extract_date(hire_date),
                            'is_active': is_active_bool,
                        }
                    )
                    if created:
                        stats['employees'] += 1
            
            # Import Salaries
            if 'Salaries' in wb.sheetnames:
                ws = wb['Salaries']
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if not any(row):
                        continue
                    employee_email, employee_name, month, base_salary, bonus, deductions, total_salary, amount_paid, status, paid_date, notes = row[:11]
                    
                    try:
                        employee = Employee.objects.get(email=employee_email)
                    except Employee.DoesNotExist:
                        continue
                    
                    month = _extract_date(month)
                    if not month:
                        continue
                    
                    _, created = EmployeeSalary.objects.update_or_create(
                        employee=employee,
                        month=month,
                        defaults={
                            'base_salary': _safe_decimal(base_salary),
                            'bonus': _safe_decimal(bonus),
                            'deductions': _safe_decimal(deductions),
                            'amount_paid': _safe_decimal(amount_paid),
                            'status': status or 'pending',
                            'paid_date': _extract_date(paid_date),
                            'notes': notes or '',
                        }
                    )
                    if created:
                        stats['salaries'] += 1
            
            # Import Debtors
            if 'Debtors' in wb.sheetnames:
                ws = wb['Debtors']
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if not any(row):
                        continue
                    name, contact_person, phone, email, address, opening_balance, current_balance, credit_limit, is_active, notes = row[:10]
                    is_active_bool = str(is_active).lower() in ['1', 'true', 'yes', 'y']
                    _, created = SundryDebtor.objects.update_or_create(
                        name=name or '',
                        defaults={
                            'contact_person': contact_person or '',
                            'phone': phone or '',
                            'email': email or '',
                            'address': address or '',
                            'opening_balance': _safe_decimal(opening_balance),
                            'current_balance': _safe_decimal(current_balance),
                            'credit_limit': _safe_decimal(credit_limit),
                            'is_active': is_active_bool,
                            'notes': notes or '',
                        }
                    )
                    if created:
                        stats['debtors'] += 1
            
            # Import Creditors
            if 'Creditors' in wb.sheetnames:
                ws = wb['Creditors']
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if not any(row):
                        continue
                    name, contact_person, phone, email, address, opening_balance, current_balance, is_active, notes = row[:9]
                    is_active_bool = str(is_active).lower() in ['1', 'true', 'yes', 'y']
                    _, created = SundryCreditor.objects.update_or_create(
                        name=name or '',
                        defaults={
                            'contact_person': contact_person or '',
                            'phone': phone or '',
                            'email': email or '',
                            'address': address or '',
                            'opening_balance': _safe_decimal(opening_balance),
                            'current_balance': _safe_decimal(current_balance),
                            'is_active': is_active_bool,
                            'notes': notes or '',
                        }
                    )
                    if created:
                        stats['creditors'] += 1
            
            msg = f"Finance import: {stats['expenses']} expenses, {stats['employees']} employees, {stats['salaries']} salaries, {stats['debtors']} debtors, {stats['creditors']} creditors"
            messages.success(request, msg)
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
    
    return redirect('gsp:data_settings')


# API ENDPOINTS
@login_required
def debtors_list_api(request):
    """API endpoint to fetch all debtors for payment selection (both active and inactive)"""
    debtors = SundryDebtor.objects.all().values('id', 'name', 'contact_person', 'phone', 'email', 'current_balance', 'is_active').order_by('name')
    return JsonResponse(list(debtors), safe=False)
