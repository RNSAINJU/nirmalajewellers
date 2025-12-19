from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView
from django.views.generic.edit import DeleteView
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.db.models import Q
from decimal import Decimal
from datetime import timedelta
import json
import nepali_datetime as ndt
from io import BytesIO
from django.contrib import messages
import openpyxl
from openpyxl.utils import get_column_letter

from .models import Order, OrderOrnament
from sales.models import Sale
from .forms import OrderForm, OrnamentFormSet
from ornament.models import Ornament

app_name = 'order'

class SearchOrnamentsAPI(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        # Only show ornaments that are still in stock (not attached to any order)
        ornaments = Ornament.objects.filter(order__isnull=True, ornament_type='stock')
        
        if query:
            ornaments = ornaments.filter(
                Q(ornament_name__icontains=query) |
                Q(code__icontains=query) |
                Q(metal_type__icontains=query)
            )
        
        data = []
        for ornament in ornaments[:20]:  # Limit to 20 results
            data.append({
                'id': ornament.id,
                'code': ornament.code or 'N/A',
                'name': ornament.ornament_name,
                'metal_type': ornament.metal_type,
                'weight': float(ornament.weight or 0),
                'jarti': float(ornament.jarti or 0),
                'jyala': float(ornament.jyala or 0),
                'gross_weight': float(ornament.gross_weight or 0),
                'stone_weight': float(ornament.stone_weight or 0),
                'diamond_weight': float(ornament.diamond_weight or 0),
                'zircon_weight': float(ornament.zircon_weight or 0),
                'amount': float(ornament.stone_totalprice or 0),
                'diamond_rate': 0.0,
                'zircon_rate': 0.0,
                'stone_rate': 0.0,
                'gold_rate': 0.0,
            })
        
        return JsonResponse({'ornaments': data})


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

    def get_queryset(self):
        """Show only orders that have not yet been converted to sales."""
        qs = super().get_queryset()
        return qs.filter(sale__isnull=True)


class OrderCreateView(CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'

    def get_initial(self):
        """Provide default dates for new orders.

        - order_date: today's Nepali date
        - deliver_date: 7 days after today's Nepali date
        """
        initial = super().get_initial()
        # Only set when not already provided (e.g., from query params or other logic)
        if 'order_date' not in initial or initial['order_date'] in (None, ''):
            try:
                initial['order_date'] = ndt.date.today()
            except Exception:
                pass

        if 'deliver_date' not in initial or initial['deliver_date'] in (None, ''):
            try:
                initial['deliver_date'] = ndt.date.today() + timedelta(days=7)
            except Exception:
                pass

        return initial

    def get_success_url(self):
        return reverse_lazy('order:list')

    def form_valid(self, form):
        # Save the order first
        self.object = form.save()

        # Create per-line OrderOrnament entries from JSON payload
        order_lines_raw = form.cleaned_data.get('order_lines_json') or '[]'
        try:
            lines = json.loads(order_lines_raw)
        except (TypeError, ValueError):
            lines = []

        for line in lines:
            ornament_id = line.get('ornament_id')
            if not ornament_id:
                continue
            try:
                ornament = Ornament.objects.get(pk=ornament_id)
            except Ornament.DoesNotExist:
                continue

            OrderOrnament.objects.create(
                order=self.object,
                ornament=ornament,
                gold_rate=Decimal(str(line.get('gold_rate', 0) or 0)),
                diamond_rate=Decimal(str(line.get('diamond_rate', 0) or 0)),
                zircon_rate=Decimal(str(line.get('zircon_rate', 0) or 0)),
                stone_rate=Decimal(str(line.get('stone_rate', 0) or 0)),
                jarti=Decimal(str(line.get('jarti', 0) or 0)),
                jyala=Decimal(str(line.get('jyala', 0) or 0)),
                line_amount=Decimal(str(line.get('line_amount', 0) or 0)),
            )

            # Also mark ornament as belonging to this order and flag as ORDER type
            ornament.order = self.object
            try:
                ornament.ornament_type = Ornament.OrnamentCategory.ORDER
            except AttributeError:
                ornament.ornament_type = 'order'
            ornament.save()

        # Recompute order totals from created lines (amount/subtotal/total/remaining)
        self.object.recompute_totals_from_lines()

        return redirect('order:list')
        
        
class OrderUpdateView(UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'

    def get_success_url(self):
        return reverse_lazy('order:list')

    def form_valid(self, form):
        # Save the order
        self.object = form.save()

        # Rebuild per-line OrderOrnament entries from JSON payload
        order_lines_raw = form.cleaned_data.get('order_lines_json') or '[]'
        try:
            lines = json.loads(order_lines_raw)
        except (TypeError, ValueError):
            lines = []

        # Clear existing lines
        self.object.order_ornaments.all().delete()

        new_ornament_ids = []
        for line in lines:
            ornament_id = line.get('ornament_id')
            if not ornament_id:
                continue
            try:
                ornament = Ornament.objects.get(pk=ornament_id)
            except Ornament.DoesNotExist:
                continue

            OrderOrnament.objects.create(
                order=self.object,
                ornament=ornament,
                gold_rate=Decimal(str(line.get('gold_rate', 0) or 0)),
                diamond_rate=Decimal(str(line.get('diamond_rate', 0) or 0)),
                zircon_rate=Decimal(str(line.get('zircon_rate', 0) or 0)),
                stone_rate=Decimal(str(line.get('stone_rate', 0) or 0)),
                jarti=Decimal(str(line.get('jarti', 0) or 0)),
                jyala=Decimal(str(line.get('jyala', 0) or 0)),
                line_amount=Decimal(str(line.get('line_amount', 0) or 0)),
            )

            # Track and mark ornaments linked to this order
            new_ornament_ids.append(ornament.id)
            ornament.order = self.object
            try:
                ornament.ornament_type = Ornament.OrnamentCategory.ORDER
            except AttributeError:
                ornament.ornament_type = 'order'
            ornament.save()

        # Detach ornaments no longer present in this order
        if new_ornament_ids:
            # Revert ornament_type back to STOCK for removed ornaments
            Ornament.objects.filter(order=self.object).exclude(id__in=new_ornament_ids).update(
                order=None,
                ornament_type='stock',
            )

        # Recompute order totals from updated lines
        self.object.recompute_totals_from_lines()

        return redirect('order:list')


class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'order/order_confirm_delete.html'
    success_url = reverse_lazy('order:list')


class CreateSaleFromOrderView(View):
    """(Deprecated here) moved to sales.views.CreateSaleFromOrderView."""

    def post(self, request, pk):
        # Thin wrapper to keep existing URLs working if still referenced.
        from sales.views import CreateSaleFromOrderView as _Create

        return _Create.as_view()(request, pk=pk)


class SalesListView(ListView):
    """(Deprecated here) moved to sales.views.SalesListView."""

    def get(self, request, *args, **kwargs):
        from sales.views import SalesListView as _List

        return _List.as_view()(request, *args, **kwargs)


class SaleUpdateView(UpdateView):
    """(Deprecated here) moved to sales.views.SaleUpdateView."""

    def dispatch(self, request, *args, **kwargs):
        from sales.views import SaleUpdateView as _Update

        return _Update.as_view()(request, *args, **kwargs)


class SaleDeleteView(DeleteView):
    """(Deprecated here) moved to sales.views.SaleDeleteView."""

    def dispatch(self, request, *args, **kwargs):
        from sales.views import SaleDeleteView as _Delete

        return _Delete.as_view()(request, *args, **kwargs)


def order_print_view(request):
    """Printable view of orders (same queryset as OrderListView)."""

    view = OrderListView()
    view.request = request
    orders = view.get_queryset()

    return render(request, "order/print_view.html", {"orders": orders})


def order_export_excel(request):
    """Export orders to Excel, similar to ornaments/purchases export."""

    view = OrderListView()
    view.request = request
    orders = view.get_queryset()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"

    headers = [
        "Order No",
        "Order Date (BS)",
        "Deliver Date (BS)",
        "Customer",
        "Phone",
        "Status",
        "Amount",
        "Discount",
        "Subtotal",
        "Tax",
        "Total",
        "Payment Mode",
        "Paid Amount",
        "Remaining Amount",
    ]
    ws.append(headers)

    for o in orders:
        ws.append([
            o.sn,
            str(o.order_date) if o.order_date else "",
            str(o.deliver_date) if o.deliver_date else "",
            o.customer_name,
            o.phone_number,
            o.get_status_display(),
            o.amount,
            o.discount,
            o.subtotal,
            o.tax,
            o.total,
            o.get_payment_mode_display(),
            o.payment_amount,
            o.remaining_amount,
        ])

    # Auto column width
    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_length + 2

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="orders.xlsx"'

    return response


def order_import_excel(request):
    """Import orders from an Excel file with columns matching export."""

    if request.method == "POST":
        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Please upload an Excel file.")
            return redirect("order:import_excel")

        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            imported = 0
            skipped = 0

            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue

                try:
                    (
                        order_no,
                        order_date_bs,
                        deliver_date_bs,
                        customer_name,
                        phone_number,
                        status,
                        amount,
                        discount,
                        subtotal,
                        tax,
                        total,
                        payment_mode,
                        paid_amount,
                        remaining_amount,
                    ) = row
                except Exception:
                    messages.error(request, "Excel format is incorrect. Columns mismatch.")
                    return redirect("order:import_excel")

                # Skip if an order with this number already exists
                if order_no and Order.objects.filter(sn=int(order_no)).exists():
                    skipped += 1
                    continue

                o = Order(
                    customer_name=customer_name or "Unknown",
                    phone_number=str(phone_number or ""),
                )

                if order_no:
                    o.sn = int(order_no)

                # Dates: NepaliDateField accepts YYYY-MM-DD strings
                if order_date_bs:
                    o.order_date = str(order_date_bs)
                if deliver_date_bs:
                    o.deliver_date = str(deliver_date_bs)

                if status in dict(Order.STATUS_CHOICES):
                    o.status = status

                o.amount = Decimal(str(amount or 0))
                o.discount = Decimal(str(discount or 0))
                o.subtotal = Decimal(str(subtotal or 0))
                o.tax = Decimal(str(tax or 0))
                o.total = Decimal(str(total or 0))
                o.payment_amount = Decimal(str(paid_amount or 0))
                o.remaining_amount = Decimal(str(remaining_amount or 0))

                if payment_mode in dict(Order.PAYMENT_CHOICES):
                    o.payment_mode = payment_mode

                o.save()
                imported += 1

            messages.success(
                request,
                f"Imported {imported} orders, skipped {skipped} duplicate/invalid rows.",
            )
            return redirect("order:list")

        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Failed to import Excel: {exc}")
            return redirect("order:import_excel")

    return render(request, "order/import_excel.html")

