from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('home/', views.index, name='home'),
    path('monthly-stock-report/', views.monthly_stock_report, name='monthly_stock_report'),
]
