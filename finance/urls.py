from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.finance_dashboard, name='finance_dashboard'),

    # Loan
    path('loans/', __import__('finance.views_loan').views_loan.loan_list, name='loan_list'),
    path('loans/add/', __import__('finance.views_loan').views_loan.loan_create, name='loan_create'),
    
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_update, name='expense_update'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('expenses/export/', views.expense_export, name='expense_export'),
    path('expenses/import/', views.expense_import, name='expense_import'),
    
    # Employees
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('employees/export/', views.employee_export, name='employee_export'),
    path('employees/import/', views.employee_import, name='employee_import'),
    
    # Salaries
    path('salaries/', views.salary_list, name='salary_list'),
    path('salaries/add/', views.salary_create, name='salary_create'),
    path('salaries/<int:pk>/edit/', views.salary_update, name='salary_update'),
    path('salaries/<int:pk>/delete/', views.salary_delete, name='salary_delete'),
    path('salaries/export/', views.salary_export, name='salary_export'),
    path('salaries/import/', views.salary_import, name='salary_import'),
    
    # Sundry Debtors
    path('debtors/', views.debtor_list, name='debtor_list'),
    path('debtors/add/', views.debtor_create, name='debtor_create'),
    path('debtors/<int:pk>/', views.debtor_detail, name='debtor_detail'),
    path('debtors/<int:pk>/edit/', views.debtor_update, name='debtor_update'),
    path('debtors/<int:pk>/delete/', views.debtor_delete, name='debtor_delete'),
    path('debtors/<int:pk>/mark-paid/', views.debtor_mark_paid, name='debtor_mark_paid'),
    path('debtors/<int:pk>/mark-unpaid/', views.debtor_mark_unpaid, name='debtor_mark_unpaid'),
    path('debtors/<int:debtor_id>/transaction/add/', views.debtor_transaction_create, name='debtor_transaction_create'),
    path('debtors/transactions/<int:pk>/edit/', views.debtor_transaction_update, name='debtor_transaction_update'),
    path('debtors/transactions/<int:pk>/delete/', views.debtor_transaction_delete, name='debtor_transaction_delete'),
    path('debtors/export/', views.debtor_export, name='debtor_export'),
    path('debtors/import/', views.debtor_import, name='debtor_import'),
    
    # Sundry Creditors
    path('creditors/', views.creditor_list, name='creditor_list'),
    path('creditors/add/', views.creditor_create, name='creditor_create'),
    path('creditors/<int:pk>/', views.creditor_detail, name='creditor_detail'),
    path('creditors/<int:pk>/edit/', views.creditor_update, name='creditor_update'),
    path('creditors/<int:pk>/delete/', views.creditor_delete, name='creditor_delete'),
    path('creditors/<int:pk>/mark-paid/', views.creditor_mark_paid, name='creditor_mark_paid'),
    path('creditors/<int:pk>/mark-unpaid/', views.creditor_mark_unpaid, name='creditor_mark_unpaid'),
    path('creditors/<int:creditor_id>/transaction/add/', views.creditor_transaction_create, name='creditor_transaction_create'),
    path('creditors/transactions/<int:pk>/edit/', views.creditor_transaction_update, name='creditor_transaction_update'),
    path('creditors/transactions/<int:pk>/delete/', views.creditor_transaction_delete, name='creditor_transaction_delete'),
    path('creditors/export/', views.creditor_export, name='creditor_export'),
    path('creditors/import/', views.creditor_import, name='creditor_import'),
    
    # Bulk Import/Export
    path('bulk-export/', views.finance_export_all, name='finance_export_all'),
    path('bulk-import/', views.finance_import_all, name='finance_import_all'),
    
    # API Endpoints
    path('api/debtors/', views.debtors_list_api, name='debtors_list_api'),
]
