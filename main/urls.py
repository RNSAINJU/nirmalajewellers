from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('home/', views.index, name='home'),
    path('monthly-stock-report/', views.monthly_stock_report, name='monthly_stock_report'),
    path('add-stock/', views.add_stock, name='add_stock'),
    path('edit-stock/<int:year>/', views.edit_stock, name='edit_stock'),
]
