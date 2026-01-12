from django.urls import path

from .views import (
    OrnamentListView,
    OrnamentCreateView,
    OrnamentUpdateView,
    OrnamentDeleteView,
    OrnamentDestroyView,
    MainCategoryCreateView,
    SubCategoryCreateView,
    KaligarCreateView,
    print_view,
    export_excel,
    import_excel,
    multiple_ornament_create,
    ornament_report,
    ornament_weight_report,
    rates_and_stock_view,
    kaligar_list,
)

app_name = 'ornament'

urlpatterns = [
    path('', OrnamentListView.as_view(), name='list'),
    path('create/', OrnamentCreateView.as_view(), name='create'),
    path('create-multiple/', multiple_ornament_create, name='create_multiple'),
    path('<int:pk>/edit/', OrnamentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', OrnamentDeleteView.as_view(), name='delete'),
    path('<int:pk>/destroy/', OrnamentDestroyView.as_view(), name='destroy'),
    path('createmaincategory/', MainCategoryCreateView.as_view(), name='createmaincategory'),
    path('createsubcategory/', SubCategoryCreateView.as_view(), name='createsubcategory'),
    path('createkaligar/', KaligarCreateView.as_view(), name='createkaligar'),
    path('kaligars/', kaligar_list, name='kaligar_list'),
    path("print/", print_view, name="print_view"),
    path("export-excel/", export_excel, name="export_excel"),
    path('import-excel/', import_excel, name='import_excel'),
    path('report/', ornament_report, name='report'),
    path('weight-report/', ornament_weight_report, name='weight_report'),
    path('rates-and-stock/', rates_and_stock_view, name='rates_and_stock'),
]

