from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView
from .models import Order
from .forms import OrderForm, OrnamentFormSet
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse
from .models import Order
from .forms import OrderForm, OrnamentFormSet
from ornament.models import Ornament
from django.views import View

app_name = 'order'

class OrnamentCreateView(View):
    template_name = 'ornament/ornament_form.html'
    success_url = reverse_lazy('ornament:list')

    def get(self, request):
        formset = OrnamentFormSet(queryset=Ornament.objects.none())
        return render(request, self.template_name, {"formset": formset})

    def post(self, request):
        formset = OrnamentFormSet(request.POST)

        if formset.is_valid():
            formset.save()
            return redirect(self.success_url)

        return render(request, self.template_name, {"formset": formset})

class OrderListView(ListView):
    model = Order
    template_name = 'order/order_list.html'
    context_object_name = 'orders'
    ordering = ['-sn']


class OrderCreateView(CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['ornament_formset'] = OrnamentFormSet(self.request.POST)
        else:
            context['ornament_formset'] = OrnamentFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        ornament_formset = context['ornament_formset']
        if ornament_formset.is_valid():
            self.object = form.save()
            ornament_formset.instance = self.object
            ornament_formset.save()
            return redirect('order:list')
        else:
            return self.render_to_response(self.get_context_data(form=form))

class OrderUpdateView(UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['ornament_formset'] = OrnamentFormSet(self.request.POST, instance=self.object)
        else:
            context['ornament_formset'] = OrnamentFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        ornament_formset = context['ornament_formset']
        if ornament_formset.is_valid():
            self.object = form.save()
            ornament_formset.instance = self.object
            ornament_formset.save()
            return redirect('order:list')
        else:
            return self.render_to_response(self.get_context_data(form=form))


class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'order/order_confirm_delete.html'
    success_url = reverse_lazy('order:list')

