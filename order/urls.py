from django.urls import path
from .views import order_list, order_create, order_update, OrderDeleteView

app_name = 'order'

urlpatterns = [
    path('', order_list, name='list'),
    path('create/', order_create, name='create'),
    path('update/<int:pk>/', order_update, name='update'),
    path('delete/<int:pk>/', OrderDeleteView.as_view(), name='delete'),
]