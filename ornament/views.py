from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Ornament
from .forms import OrnamentForm


class OrnamentListView(ListView):
    model = Ornament
    template_name = 'ornament/ornament_list.html'
    context_object_name = 'ornaments'
    ordering = ['-ornament_date', '-created_at']


class OrnamentCreateView(CreateView):
    model = Ornament
    fields=[
    'ornament_date', 'code', 'ornament_name', 'type', 'weight', 'diamond_weight', 'jarti', 'kaligar', 'ornament_type', 'customer_name'
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