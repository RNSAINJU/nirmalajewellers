from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView
from .models import Order
from .forms import OrderForm, OrnamentFormSet
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse
from .models import Order
from .forms import OrderForm, OrnamentFormSet


app_name = 'order'


class OrderListView(ListView):
    model = Order
    template_name = 'order/order_list.html'
    context_object_name = 'orders'
    ordering = ['-sn']

# To add a button for "Add Ornament" on the OrderCreate page,
# We typically add context data or signals for where the button should be displayed,
# but the main work is to make sure the context in OrderCreateView gives the formset.
# The button itself is added in the template, but for the backend, you may want to pass extra context.

# However, to assist template rendering, we can add a context variable here
# indicating this is the create view (helpful for templates).

# No backend code is strictly necessary for a button, but for good practice:
def get_context_data(self, **kwargs):
    context = super(OrderCreateView, self).get_context_data(**kwargs)
    if self.request.POST:
        context['ornament_formset'] = OrnamentFormSet(self.request.POST)
    else:
        context['ornament_formset'] = OrnamentFormSet()
    context['show_add_ornament_button'] = True  # Template flag for button display
    return context

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

