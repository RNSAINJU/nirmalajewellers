from django.urls import path
from .views import (
    PartyCreateView, PurchaseListView, PurchaseCreateView,
    PurchaseUpdateView, PurchaseDeleteView,
    CustomerPurchaseListView, CustomerPurchaseCreateView,
    CustomerPurchaseUpdateView, CustomerPurchaseDeleteView,
    export_excel, print_view, import_excel,
    export_customer_excel, import_customer_excel
)

app_name = 'gsp'

urlpatterns = [
    path('', PurchaseListView.as_view(), name='purchaselist'),
    path('create/', PurchaseCreateView.as_view(), name='createpurchase'),
    path('createparty/', PartyCreateView.as_view(), name='createparty'),
    path('<int:pk>/edit/', PurchaseUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', PurchaseDeleteView.as_view(), name='delete'),
    path('customer-purchases/', CustomerPurchaseListView.as_view(), name='customer_purchase_list'),
    path('customer-purchases/create/', CustomerPurchaseCreateView.as_view(), name='customer_purchase_create'),
    path('customer-purchases/<int:pk>/edit/', CustomerPurchaseUpdateView.as_view(), name='customer_purchase_update'),
    path('customer-purchases/<int:pk>/delete/', CustomerPurchaseDeleteView.as_view(), name='customer_purchase_delete'),
    path('customer-purchases/export-excel/', export_customer_excel, name='customer_export_excel'),
    path('customer-purchases/import-excel/', import_customer_excel, name='customer_import_excel'),
    path("print/", print_view, name="print_view"),
    path("export-excel/", export_excel, name="export_excel"),
    path('import-excel/', import_excel, name='gsp_import_excel'),
]
