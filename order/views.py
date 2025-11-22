from django.shortcuts import  render, get_object_or_404, redirect
from django.urls import path, reverse_lazy
from .models import  Order
from .forms import OrderForm
from django.views.generic.edit import DeleteView

app_name = 'order'

def order_list(request):
    orders = Order.objects.all()
    return render(request, 'order/order_list.html', {'orders': orders})


def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('order:list')
    else:
        form = OrderForm()
    return render(request, 'order/order_form.html', {'form': form, 'form_title': 'Create Order'})

def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order:list')
    else:
        form = OrderForm(instance=order)
    return render(request, 'order/order_form.html', {'form': form, 'form_title': 'Update Order'})

class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'order/order_confirm_delete.html'
    success_url = reverse_lazy('order:list')
