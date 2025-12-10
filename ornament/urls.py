from django.urls import path

from .views import (
    OrnamentListView,
    OrnamentCreateView,
    OrnamentUpdateView,
    OrnamentDeleteView,
    MainCategoryCreateView,
    SubCategoryCreateView,
    KaligarCreateView
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
]

