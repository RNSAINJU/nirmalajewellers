from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_update, name='expense_update'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    
    # Employees
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    
    # Salaries
    path('salaries/', views.salary_list, name='salary_list'),
    path('salaries/add/', views.salary_create, name='salary_create'),
    path('salaries/<int:pk>/edit/', views.salary_update, name='salary_update'),
    path('salaries/<int:pk>/delete/', views.salary_delete, name='salary_delete'),
    
    # Sundry Debtors
    path('debtors/', views.debtor_list, name='debtor_list'),
    path('debtors/add/', views.debtor_create, name='debtor_create'),
    path('debtors/<int:pk>/', views.debtor_detail, name='debtor_detail'),
    path('debtors/<int:pk>/edit/', views.debtor_update, name='debtor_update'),
    path('debtors/<int:pk>/delete/', views.debtor_delete, name='debtor_delete'),
    path('debtors/<int:debtor_id>/transaction/add/', views.debtor_transaction_create, name='debtor_transaction_create'),
    
    # Sundry Creditors
    path('creditors/', views.creditor_list, name='creditor_list'),
    path('creditors/add/', views.creditor_create, name='creditor_create'),
    path('creditors/<int:pk>/', views.creditor_detail, name='creditor_detail'),
    path('creditors/<int:pk>/edit/', views.creditor_update, name='creditor_update'),
    path('creditors/<int:pk>/delete/', views.creditor_delete, name='creditor_delete'),
    path('creditors/<int:creditor_id>/transaction/add/', views.creditor_transaction_create, name='creditor_transaction_create'),
    
    # API Endpoints
    path('api/debtors/', views.debtors_list_api, name='debtors_list_api'),
]
