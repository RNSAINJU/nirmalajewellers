from django.urls import path
from . import views

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
]
