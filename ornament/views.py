from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Sum, Q
from .models import Ornament
from .forms import OrnamentForm


class OrnamentListView(ListView):
    model = Ornament
    template_name = 'ornament/ornament_list.html'
    context_object_name = 'ornaments'
    ordering = ['-ornament_date', '-created_at']
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        # --- Filters ---
        code = self.request.GET.get("code")
        name = self.request.GET.get("name")
        customer = self.request.GET.get("customer")
        otype = self.request.GET.get("type")
        ornament_type = self.request.GET.get("otype")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        # Search Filters
        if code:
            qs = qs.filter(code__icontains=code)

        if name:
            qs = qs.filter(ornament_name__icontains=name)

        if customer:
            qs = qs.filter(customer_name__icontains=customer)

        # Dropdown Filters
        if otype:
            qs = qs.filter(type=otype)

        if ornament_type:
            qs = qs.filter(ornament_type=ornament_type)

        # Nepali Date Filter: exact match (since NepaliDateField is string)
        if start_date and end_date:
            qs = qs.filter(ornament_date__gte=start_date,
                           ornament_date__lte=end_date)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = context['ornaments']

        # Total weight (rounded, no decimals)
        total_weight = qs.aggregate(total=Sum('weight'))['total'] or 0
        context['total_weight'] = round(total_weight)

        return context


class OrnamentCreateView(CreateView):
    model = Ornament
    fields = [
        'ornament_date', 'code', 'ornament_name', 'type', 'weight',
        'diamond_weight', 'jarti', 'kaligar', 'ornament_type', 'customer_name'
    ]
    template_name = 'ornament/ornament_form.html'
    success_url = reverse_lazy('ornament:list')


class OrnamentUpdateView(UpdateView):
    model = Ornament
    form_class = OrnamentForm
    template_name = 'ornament/ornament_form.html'
    success_url = reverse_lazy('ornament:list')


class OrnamentDeleteView(DeleteView):
    model = Ornament
    template_name = 'ornament/ornament_confirm_delete.html'
    success_url = reverse_lazy('ornament:list')
