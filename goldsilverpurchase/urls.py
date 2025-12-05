from django.urls import path
from .views import (
    PartyCreateView, PurchaseListView, PurchaseCreateView,
    PurchaseUpdateView, PurchaseDeleteView
)

app_name = 'gsp'

urlpatterns = [
    path('', PurchaseListView.as_view(), name='list'),
    path('create/', PurchaseCreateView.as_view(), name='create'),
    path('createparty/', PartyCreateView.as_view(), name='createparty'),
    path('<int:pk>/edit/', PurchaseUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', PurchaseDeleteView.as_view(), name='delete'),
]
