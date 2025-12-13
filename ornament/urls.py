from django.urls import path

from .views import (
    OrnamentListView,
    OrnamentCreateView,
    OrnamentUpdateView,
    OrnamentDeleteView,
    MainCategoryCreateView,
    SubCategoryCreateView,
    KaligarCreateView,
    print_view,
    export_excel,
    import_excel
)

app_name = 'ornament'

urlpatterns = [
    path('', OrnamentListView.as_view(), name='list'),
    path('create/', OrnamentCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', OrnamentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', OrnamentDeleteView.as_view(), name='delete'),
    path('createmaincategory/', MainCategoryCreateView.as_view(), name='createmaincategory'),
    path('createsubcategory/', SubCategoryCreateView.as_view(), name='createsubcategory'),
    path('createkaligar/', KaligarCreateView.as_view(), name='createkaligar'),
    path("print/", print_view, name="print_view"),
    path("export-excel/", export_excel, name="export_excel"),
    path('import-excel/', import_excel, name='import_excel'),
]

