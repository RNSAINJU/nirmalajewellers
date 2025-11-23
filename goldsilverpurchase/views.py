from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import GoldSilverPurchase


class PurchaseListView(ListView):
    model = GoldSilverPurchase
    template_name = 'goldsilverpurchase/purchase_list.html'
    context_object_name = 'purchases'
    ordering = ['-bill_date', '-created_at']


class PurchaseCreateView(CreateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party_name', 'panno',
        'particular', 'metal_type', 'quantity',
        'rate', 'wages', 'amount', 'payment_mode'
    ]
    template_name = 'goldsilverpurchase/purchase_form.html'
    success_url = reverse_lazy('gsp:list')


class PurchaseUpdateView(UpdateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party_name', 'panno',
        'particular', 'metal_type', 'quantity',
        'rate', 'wages', 'amount', 'payment_mode'
    ]
    template_name = 'goldsilverpurchase/purchase_form.html'
    success_url = reverse_lazy('gsp:list')


class PurchaseDeleteView(DeleteView):
    model = GoldSilverPurchase
    template_name = 'goldsilverpurchase/purchase_confirm_delete.html'
    success_url = reverse_lazy('gsp:list')
