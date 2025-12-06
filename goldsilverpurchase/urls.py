from django.urls import path
from .views import (
    PartyCreateView, PurchaseListView, PurchaseCreateView,
    PurchaseUpdateView, PurchaseDeleteView, 
    export_excel, print_view, import_excel
)

app_name = 'gsp'

urlpatterns = [
    path('', PurchaseListView.as_view(), name='list'),
    path('create/', PurchaseCreateView.as_view(), name='create'),
    path('createparty/', PartyCreateView.as_view(), name='createparty'),
    path('<int:pk>/edit/', PurchaseUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', PurchaseDeleteView.as_view(), name='delete'),
    path("print/", print_view, name="print_view"),
    path("export-excel/", export_excel, name="export_excel"),
    path('import-excel/', import_excel, name='gsp_import_excel'),
]
