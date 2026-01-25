from django.urls import path
from .views_ajax import get_metal_stock_balance
from .views import (
    OrderListView,
    OrderCreateView,
    OrderUpdateView,
    OrderDeleteView,
    SearchOrnamentsAPI,
    CreateOrnamentInlineView,
    CreateSaleFromOrderView,
    SalesListView,
    SaleUpdateView,
    SaleDeleteView,
    order_print_view,
    order_export_excel,
    order_import_excel,
    order_ornaments_export_excel,
    order_payments_export_excel,
    order_ornaments_import_excel,
    order_payments_import_excel,
)
from .reports import (
    OrderDashboardReport,
    OrderSalesAnalysis,
    OrderPaymentAnalysis,
    OrderMetalAnalysis,
    OrderCustomerAnalysis,
)

app_name = 'order'

urlpatterns = [
    path('ajax/metal-stock-balance/', get_metal_stock_balance, name='ajax_metal_stock_balance'),
    path('', OrderListView.as_view(), name='list'),
    path('create/', OrderCreateView.as_view(), name='create'),
    path('update/<int:pk>/', OrderUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', OrderDeleteView.as_view(), name='delete'),
    path('print/', order_print_view, name='print_view'),
    path('export-excel/', order_export_excel, name='export_excel'),
    path('import-excel/', order_import_excel, name='import_excel'),
    path('export-order-ornaments/', order_ornaments_export_excel, name='export_order_ornaments'),
    path('export-order-payments/', order_payments_export_excel, name='export_order_payments'),
    path('import-order-ornaments/', order_ornaments_import_excel, name='import_order_ornaments'),
    path('import-order-payments/', order_payments_import_excel, name='import_order_payments'),
    path('sales/', SalesListView.as_view(), name='sales_list'),
    path('sales/create-from-order/<int:pk>/', CreateSaleFromOrderView.as_view(), name='create_sale_from_order'),
    path('sales/<int:pk>/edit/', SaleUpdateView.as_view(), name='sale_update'),
    path('sales/<int:pk>/delete/', SaleDeleteView.as_view(), name='sale_delete'),
    path('api/search-ornaments/', SearchOrnamentsAPI.as_view(), name='search_ornaments'),
    path('api/create-ornament-inline/', CreateOrnamentInlineView.as_view(), name='create_ornament_inline'),
    # Report URLs
    path('reports/dashboard/', OrderDashboardReport.as_view(), name='dashboard_report'),
    path('reports/sales/', OrderSalesAnalysis.as_view(), name='sales_report'),
    path('reports/payments/', OrderPaymentAnalysis.as_view(), name='payment_report'),
    path('reports/metals/', OrderMetalAnalysis.as_view(), name='metal_report'),
    path('reports/customers/', OrderCustomerAnalysis.as_view(), name='customer_report'),
]