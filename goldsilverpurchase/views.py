from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import GoldSilverPurchase, Party
from django.db.models import Sum
import nepali_datetime as ndt

class PurchaseListView(ListView):
    model = GoldSilverPurchase
    template_name = 'goldsilverpurchase/purchase_list.html'
    context_object_name = 'purchases'
    ordering = ['-bill_date', '-created_at']
    paginate_by = 20  # 20 purchases per page

    def get_queryset(self):
        queryset = super().get_queryset()
        date_str = self.request.GET.get('date')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        party_id = self.request.GET.get('party')

        # Single date filter
        if date_str:
            try:
                y, m, d = map(int, date_str.split('-'))
                date = ndt.date(y, m, d)
                queryset = queryset.filter(bill_date=date)
            except ValueError:
                pass

        # Date range filter
        elif start_date_str and end_date_str:
            try:
                y1, m1, d1 = map(int, start_date_str.split('-'))
                y2, m2, d2 = map(int, end_date_str.split('-'))
                start_date = ndt.date(y1, m1, d1)
                end_date = ndt.date(y2, m2, d2)
                queryset = queryset.filter(bill_date__range=(start_date, end_date))
            except ValueError:
                pass

        # Party filter
        if party_id:
            queryset = queryset.filter(party_id=party_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_amount'] = self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0
        context['date'] = self.request.GET.get('date', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['parties'] = Party.objects.all()
        context['selected_party'] = self.request.GET.get('party', '')
        return context

class PartyCreateView(CreateView):
    model = Party
    fields = ['party_name', 'panno']
    template_name = 'goldsilverpurchase/party_form.html'
    success_url = reverse_lazy('gsp:list')


class PurchaseCreateView(CreateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party',
        'particular', 'metal_type', 'quantity',
        'rate', 'wages', 'discount','amount', 'payment_mode'
    ]
    template_name = 'goldsilverpurchase/purchase_form.html'
    success_url = reverse_lazy('gsp:list')


class PurchaseUpdateView(UpdateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party',
        'particular', 'metal_type', 'quantity',
        'rate', 'wages','discount', 'amount', 'payment_mode'
    ]
    template_name = 'goldsilverpurchase/purchase_form.html'
    success_url = reverse_lazy('gsp:list')


class PurchaseDeleteView(DeleteView):
    model = GoldSilverPurchase
    template_name = 'goldsilverpurchase/purchase_confirm_delete.html'
    success_url = reverse_lazy('gsp:list')
