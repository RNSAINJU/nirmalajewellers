from django.urls import path
from . import views
from . import views_accounts
from . import views_assets

app_name = 'main'

urlpatterns = [
    path('', views.customer_home, name='customer_home'),
    path('admin-dashboard/', views.dashboard, name='dashboard'),
    path('home/', views.index, name='home'),
    path('stock-report/', views.stock_report, name='stock_report'),
    path('monthly-stock-report/', views.monthly_stock_report, name='monthly_stock_report'),
    path('daily-rates/', views.daily_rates, name='daily_rates'),
    path('daily-rates/add/', views.add_daily_rate, name='add_daily_rate'),
    path('daily-rates/<int:pk>/edit/', views.edit_daily_rate, name='edit_daily_rate'),
    path('daily-rates/<int:pk>/delete/', views.delete_daily_rate, name='delete_daily_rate'),
    path('add-stock/', views.add_stock, name='add_stock'),
    path('edit-stock/<int:year>/', views.edit_stock, name='edit_stock'),
    
    # Customer API Endpoints
    path('api/products/by-category/<int:category_id>/', views.api_products_by_category, name='api_products_by_category'),
    path('api/products/search/', views.api_search_products, name='api_search_products'),
    path('api/products/featured/', views.api_featured_products, name='api_featured_products'),
    
    # Customer Page Routes
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('shop/', views.category_products, name='shop'),
    path('shop/category/<int:category_id>/', views.category_products, name='category_products'),
    path('cart/', views.cart, name='cart'),
    
    # Account Management URLs
    path('account-settings/', views_accounts.account_settings, name='account_settings'),
    path('users/create/', views_accounts.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views_accounts.user_update, name='user_update'),
    path('users/<int:user_id>/delete/', views_accounts.user_delete, name='user_delete'),
    path('users/<int:user_id>/change-password/', views_accounts.user_change_password, name='user_change_password'),
    
    # User Profile URLs (for logged-in user to edit their own profile)
    path('profile/', views_accounts.user_profile, name='user_profile'),
    path('profile/change-password/', views_accounts.user_profile_change_password, name='user_profile_change_password'),
    
    # Role Management URLs
    path('roles/', views_accounts.role_list, name='role_list'),
    path('roles/create/', views_accounts.role_create, name='role_create'),
    path('roles/<int:role_id>/edit/', views_accounts.role_update, name='role_update'),
    path('roles/<int:role_id>/delete/', views_accounts.role_delete, name='role_delete'),
    
    # Assets URLs
    path('total-assets/', views_assets.total_assets, name='total_assets'),
]
