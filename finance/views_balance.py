from django.shortcuts import render
from django.db.models import Sum
from finance.models import CreditorTransaction, DebtorTransaction, EmployeeSalary
from order.models import Order
from sales.models import Sale

def balance_sheet(request):
    # Example: You may need to adjust these queries to fit your models
    creditors = CreditorTransaction.objects.aggregate(total=Sum('amount'))['total'] or 0
    debtors = DebtorTransaction.objects.aggregate(total=Sum('amount'))['total'] or 0
    salaries = EmployeeSalary.objects.aggregate(total=Sum('amount'))['total'] or 0
    order_income = Order.objects.aggregate(total=Sum('total'))['total'] or 0
    sales_income = Sale.objects.aggregate(total=Sum('total'))['total'] or 0

    assets = debtors + order_income + sales_income
    liabilities = creditors + salaries
    equity = assets - liabilities

    context = {
        'assets': assets,
        'liabilities': liabilities,
        'equity': equity,
        'creditors': creditors,
        'debtors': debtors,
        'salaries': salaries,
        'order_income': order_income,
        'sales_income': sales_income,
    }
    return render(request, 'finance/balance_sheet.html', context)
