from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Sum
from .models import Kaligar, Ornament
from .forms import OrnamentForm


class OrnamentListView(ListView):
    model = Ornament
    template_name = 'ornament/ornament_list.html'
    context_object_name = 'ornaments'
    ordering = ['-ornament_date', '-created_at']

    def get_queryset(self):
        qs = super().get_queryset()

        # Filters
        code = self.request.GET.get("code")
        name = self.request.GET.get("name")
        customer = self.request.GET.get("customer")
        type = self.request.GET.get("type")
        ornament_type = self.request.GET.get("ornament_type")
        metal_type = self.request.GET.get("metal_type")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        kaligar_id = self.request.GET.get('kaligar')

        if code:
            qs = qs.filter(code__icontains=code)

        if name:
            qs = qs.filter(ornament_name__icontains=name)

        if type:
            qs = qs.filter(type=type)

        if ornament_type:
            qs = qs.filter(ornament_type=ornament_type)

        if metal_type:
            qs = qs.filter(metal_type=metal_type)

        if kaligar_id:
            qs = qs.filter(kaligar_id=kaligar_id)

        if start_date and end_date:
            qs = qs.filter(
                ornament_date__gte=start_date,
                ornament_date__lte=end_date
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = context['ornaments']

        # Total weight calculation
        context['total_weight'] = qs.aggregate(total=Sum('weight'))['total'] or 0

        # Filters back to template
        context['metal_type'] = self.request.GET.get('metal_type')
        context['ornament_type'] = self.request.GET.get('ornament_type')
        context['type'] = self.request.GET.get('type')

        # Kaligar list
        context['kaligar'] = Kaligar.objects.all()
        context['selected_kaligar'] = self.request.GET.get('kaligar', '')

        return context


class OrnamentCreateView(CreateView):
    model = Ornament
    form_class = OrnamentForm
    template_name = 'ornament/ornament_form.html'
    success_url = reverse_lazy('ornament:list')

    def form_valid(self, form):
        # Cloudinary image is automatically handled by ModelForm
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['JARTI_CHOICES'] = [
            (4.0, "4%"),
            (4.5, "4.5%"),
            (5.0, "5%"),
            (6.5, "6.5%"),
            (8.0, "8%"),
        ]
        return context


class OrnamentUpdateView(UpdateView):
    model = Ornament
    form_class = OrnamentForm
    template_name = 'ornament/ornament_form.html'
    success_url = reverse_lazy('ornament:list')

    def form_valid(self, form):
        # Cloudinary image is automatically handled by ModelForm
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['JARTI_CHOICES'] = [
            (4.0, "4%"),
            (4.5, "4.5%"),
            (5.0, "5%"),
            (6.5, "6.5%"),
            (8.0, "8%"),
        ]
        return context


class OrnamentDeleteView(DeleteView):
    model = Ornament
    template_name = 'ornament/ornament_confirm_delete.html'
    success_url = reverse_lazy('ornament:list')
