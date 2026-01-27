from django.urls import path
from . import views
from . import views_accounts

app_name = 'main'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('home/', views.index, name='home'),
    path('stock-report/', views.stock_report, name='stock_report'),
    path('monthly-stock-report/', views.monthly_stock_report, name='monthly_stock_report'),
    path('daily-rates/', views.daily_rates, name='daily_rates'),
    path('daily-rates/add/', views.add_daily_rate, name='add_daily_rate'),
    path('daily-rates/<int:pk>/edit/', views.edit_daily_rate, name='edit_daily_rate'),
    path('daily-rates/<int:pk>/delete/', views.delete_daily_rate, name='delete_daily_rate'),
    path('add-stock/', views.add_stock, name='add_stock'),
    path('edit-stock/<int:year>/', views.edit_stock, name='edit_stock'),
    
    # Account Management URLs
    path('account-settings/', views_accounts.account_settings, name='account_settings'),
    path('users/create/', views_accounts.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views_accounts.user_update, name='user_update'),
    path('users/<int:user_id>/delete/', views_accounts.user_delete, name='user_delete'),
    path('users/<int:user_id>/change-password/', views_accounts.user_change_password, name='user_change_password'),
    
    # Role Management URLs
    path('roles/', views_accounts.role_list, name='role_list'),
    path('roles/create/', views_accounts.role_create, name='role_create'),
    path('roles/<int:role_id>/edit/', views_accounts.role_update, name='role_update'),
    path('roles/<int:role_id>/delete/', views_accounts.role_delete, name='role_delete'),
]
