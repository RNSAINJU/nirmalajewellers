from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView
from .models import Order
from .forms import OrderForm, OrnamentFormSet

app_name = 'order'

class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'order/order_confirm_delete.html'
    success_url = reverse_lazy('order:list')

def order_list(request):
    orders = Order.objects.prefetch_related('ornaments').all()
    return render(request, 'order/order_list.html', {'orders': orders})

def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrnamentFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save()
            formset.instance = order
            formset.save()
            return redirect('order:list')
    else:
        form = OrderForm()
        formset = OrnamentFormSet()
    return render(request, 'order/order_form.html', {
        'form': form,
        'formset': formset,
        'form_title': 'Create Order'
    })

def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrnamentFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('order:list')
    else:
        form = OrderForm(instance=order)
        formset = OrnamentFormSet(instance=order)
    return render(request, 'order/order_form.html', {
        'form': form,
        'formset': formset,
        'form_title': 'Update Order'
    })
