from django.urls import path

from .views import (
    CreateSaleFromOrderView,
    SalesListView,
    SaleUpdateView,
    SaleDeleteView,
    DirectSaleCreateView,
    sales_print_view,
    sales_export_excel,
    sales_import_excel,
    DeleteSaleAndOrderView,
    download_import_template,
    ImportWizardStepOneView,
    ImportWizardStepTwoView,
    ImportWizardStepThreeView,
)

app_name = "sales"

urlpatterns = [
    path("", SalesListView.as_view(), name="sales_list"),
    path("create/", DirectSaleCreateView.as_view(), name="sale_create"),
    path("create-from-order/<int:pk>/", CreateSaleFromOrderView.as_view(), name="create_sale_from_order"),
    path("print/", sales_print_view, name="print_view"),
    path("export-excel/", sales_export_excel, name="export_excel"),
    path("import-excel/", sales_import_excel, name="import_excel"),
    # Import wizard (3-step process)
    path("import-wizard/", ImportWizardStepOneView.as_view(), name="import_wizard_step1"),
    path("import-wizard/upload/", ImportWizardStepTwoView.as_view(), name="import_wizard_step2"),
    path("import-wizard/confirm/", ImportWizardStepThreeView.as_view(), name="import_wizard_step3"),
    path("import-template/download/", download_import_template, name="download_import_template"),
    path("<int:pk>/delete-order/", DeleteSaleAndOrderView.as_view(), name="sale_delete_with_order"),
    path("<int:pk>/edit/", SaleUpdateView.as_view(), name="sale_update"),
    path("<int:pk>/delete/", SaleDeleteView.as_view(), name="sale_delete"),
]
