from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from decimal import Decimal
from datetime import timedelta
from io import BytesIO
import json
import nepali_datetime as ndt
from django.http import HttpResponse
from django.contrib import messages
import openpyxl
from openpyxl.utils import get_column_letter
from django.db.models import Sum

from order.models import Order, OrderOrnament, OrderPayment
from order.forms import OrderForm, OrnamentFormSet
from ornament.models import Ornament
from .models import Sale


class CreateSaleFromOrderView(View):
    """Create a Sale entry from an existing Order.

    This is triggered from the order list via a button. If a Sale already
    exists for the given order, it simply redirects without creating a
    duplicate.
    """

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        # If sale already exists for this order, do nothing
        if hasattr(order, "sale") and order.sale is not None:
            return redirect("order:list")

        # Prefer deliver_date, then order_date, otherwise today's Nepali date
        sale_date = order.deliver_date or order.order_date
        if sale_date is None:
            try:
                sale_date = ndt.date.today()
            except Exception:
                sale_date = None

        # Default bill number for the sale (can be edited later)
        bill_no = str(order.sn)

        # Create the Sale record
        Sale.objects.create(order=order, sale_date=sale_date, bill_no=bill_no)

        # Mark ornaments on this order as sales items
        Ornament.objects.filter(order=order).update(
            ornament_type=Ornament.OrnamentCategory.SALES
        )

        # Mark the order as delivered once it is added to sales
        order.status = "delivered"
        order.save(update_fields=["status", "updated_at"])

        return redirect("order:list")


class SalesListView(ListView):
    """List all Sales with their related Orders."""

    model = Sale
    template_name = "sales/sales_list.html"
    context_object_name = "sales"
    ordering = ["-bill_no"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("order")
            .annotate(total_weight=Sum("order__ornaments__weight"))
            .prefetch_related("order__ornaments")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sales_count"] = Sale.objects.count()

        purity_factors = {
            Ornament.TypeCategory.TWENTYFOURKARAT: Decimal("1.00"),
            Ornament.TypeCategory.TWENTHREEKARAT: Decimal("0.99"),
            Ornament.TypeCategory.TWENTYTWOKARAT: Decimal("0.98"),
            Ornament.TypeCategory.EIGHTEENKARAT: Decimal("0.75"),
            Ornament.TypeCategory.FOURTEENKARAT: Decimal("0.58"),
        }

        gold_lines = OrderOrnament.objects.filter(
            order__sale__isnull=False,
            ornament__metal_type=Ornament.MetalTypeCategory.GOLD,
        ).select_related("ornament")

        gold_24_weight = Decimal("0")
        for line in gold_lines:
            weight = line.ornament.weight or Decimal("0")
            factor = purity_factors.get(line.ornament.type, Decimal("1.00"))
            gold_24_weight += weight * factor

        silver_weight = (
            OrderOrnament.objects.filter(
                order__sale__isnull=False,
                ornament__metal_type=Ornament.MetalTypeCategory.SILVER,
            )
            .aggregate(total=Sum("ornament__weight"))
            .get("total")
            or Decimal("0")
        )

        total_sales_amount = (
            Order.objects.filter(sale__isnull=False)
            .aggregate(total=Sum("total"))
            .get("total")
            or Decimal("0")
        )

        context.update(
            {
                "gold_24_weight": gold_24_weight,
                "silver_weight": silver_weight,
                "total_sales_amount": total_sales_amount,
            }
        )

        return context


class SaleUpdateView(UpdateView):
    """Edit a Sale (bill number and sale date)."""

    model = Sale
    fields = ["bill_no", "sale_date"]
    template_name = "sales/sale_form.html"

    def get_success_url(self):
        return reverse_lazy("sales:sales_list")


class SaleDeleteView(DeleteView):
    """Delete a Sale and return the order to the open orders list."""

    model = Sale
    template_name = "sales/sale_confirm_delete.html"
    success_url = reverse_lazy("sales:sales_list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        order = self.object.order
        response = super().delete(request, *args, **kwargs)

        # Reset order status so it is no longer treated as delivered
        order.status = "order"
        order.save(update_fields=["status", "updated_at"])

        return response


class DeleteSaleAndOrderView(View):
    """Delete both the Sale and its related Order.

    Also returns all ornaments on that order back to stock by clearing
    their order FK and setting ornament_type to STOCK.
    """

    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        order = sale.order

        if order is not None:
            # Return ornaments on this order back to stock
            Ornament.objects.filter(order=order).update(
                order=None,
                ornament_type=Ornament.OrnamentCategory.STOCK,
            )

            # Deleting the order will cascade to the Sale via FK
            order.delete()
        else:
            # Fallback: just delete the sale if order is missing
            sale.delete()

        return redirect("sales:sales_list")


class DirectSaleCreateView(CreateView):
    """Create a new Order + Sale in one step, using the same
    auto-calculation and ornament selection logic as the Order
    create page, but finalizing it directly as a Sale.
    """

    model = Order
    form_class = OrderForm
    template_name = "order/order_form.html"

    def get_initial(self):
        initial = super().get_initial()
        if "order_date" not in initial or initial["order_date"] in (None, ""):
            try:
                initial["order_date"] = ndt.date.today()
            except Exception:
                pass

        if "deliver_date" not in initial or initial["deliver_date"] in (None, ""):
            try:
                initial["deliver_date"] = ndt.date.today() + timedelta(days=7)
            except Exception:
                pass

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Indicate that this is a sales create page so the shared
        # template can hide order-specific bits and show sales fields.
        context["is_sale_create"] = True
        context.setdefault("form_title", "Create Sale")
        context["payment_choices"] = Order.PAYMENT_CHOICES
        context["initial_payments_json"] = json.dumps([])

        # Provide defaults for sale-specific fields
        try:
            default_sale_date = ndt.date.today()
        except Exception:
            default_sale_date = ""

        context.setdefault("sale_date", default_sale_date)
        context.setdefault("bill_no", "")
        return context

    def get_success_url(self):
        return reverse_lazy("sales:sales_list")

    def form_valid(self, form):
        # Save the order first
        self.object = form.save()

        # Create per-line OrderOrnament entries from JSON payload
        order_lines_raw = form.cleaned_data.get("order_lines_json") or "[]"
        try:
            lines = json.loads(order_lines_raw)
        except (TypeError, ValueError):
            lines = []

        for line in lines:
            ornament_id = line.get("ornament_id")
            if not ornament_id:
                continue
            try:
                ornament = Ornament.objects.get(pk=ornament_id)
            except Ornament.DoesNotExist:
                continue

            OrderOrnament.objects.create(
                order=self.object,
                ornament=ornament,
                gold_rate=Decimal(str(line.get("gold_rate", 0) or 0)),
                diamond_rate=Decimal(str(line.get("diamond_rate", 0) or 0)),
                zircon_rate=Decimal(str(line.get("zircon_rate", 0) or 0)),
                stone_rate=Decimal(str(line.get("stone_rate", 0) or 0)),
                jarti=Decimal(str(line.get("jarti", 0) or 0)),
                jyala=Decimal(str(line.get("jyala", 0) or 0)),
                line_amount=Decimal(str(line.get("line_amount", 0) or 0)),
            )

            # Also mark ornament as belonging to this order and flag as ORDER type
            ornament.order = self.object
            try:
                ornament.ornament_type = Ornament.OrnamentCategory.SALES
            except AttributeError:
                ornament.ornament_type = "sales"
            ornament.save()

        # Persist payment breakdown for the sale
        payment_lines_raw = form.cleaned_data.get("payment_lines_json") or "[]"
        try:
            payments_data = json.loads(payment_lines_raw)
        except (TypeError, ValueError):
            payments_data = []

        self.object.payments.all().delete()
        for payment in payments_data:
            amount = Decimal(str(payment.get("amount", 0) or 0))
            if amount <= 0:
                continue
            mode = payment.get("payment_mode") or payment.get("mode") or "cash"
            if mode not in dict(Order.PAYMENT_CHOICES):
                mode = "cash"
            OrderPayment.objects.create(
                order=self.object,
                payment_mode=mode,
                amount=amount,
            )

        # Recompute order totals from created lines (amount/subtotal/total/remaining)
        self.object.recompute_totals_from_lines()

        # Immediately create a Sale for this order using sales-specific
        # fields from the form when provided.
        raw_sale_date = self.request.POST.get("sale_date") or None
        bill_no = self.request.POST.get("bill_no") or str(self.object.sn)

        if raw_sale_date:
            sale_date = raw_sale_date
        else:
            sale_date = self.object.deliver_date or self.object.order_date
            if sale_date is None:
                try:
                    sale_date = ndt.date.today()
                except Exception:
                    sale_date = None

        Sale.objects.create(order=self.object, sale_date=sale_date, bill_no=bill_no)

        # Mark order as delivered for direct sales
        self.object.status = "delivered"
        self.object.save(update_fields=["status", "updated_at"])

        return redirect(self.get_success_url())


def sales_print_view(request):
    """Printable view of sales (with related orders)."""

    view = SalesListView()
    view.request = request
    sales = view.get_queryset()

    return render(request, "sales/print_view.html", {"sales": sales})


def sales_export_excel(request):
    """Export sales to Excel, similar to ornaments/purchases export."""

    view = SalesListView()
    view.request = request
    sales = view.get_queryset()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales"

    headers = [
        "Bill No",
        "Sale Date (BS)",
        "Order No",
        "Order Date (BS)",
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

    for s in sales:
        o = s.order
        ws.append([
            s.bill_no,
            str(s.sale_date) if s.sale_date else "",
            o.sn,
            str(o.order_date) if o.order_date else "",
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
    response["Content-Disposition"] = 'attachment; filename="sales.xlsx"'

    return response


def sales_import_excel(request):
    """Import sales from Excel.

    Expected columns (in order):
    Bill No, Sale Date (BS), Order No
    """

    if request.method == "POST":
        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Please upload an Excel file.")
            return redirect("sales:import_excel")

        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            imported = 0
            skipped = 0

            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue

                try:
                    bill_no, sale_date_bs, order_no = row[:3]
                except Exception:
                    messages.error(request, "Excel format is incorrect. Columns mismatch.")
                    return redirect("sales:import_excel")

                if not order_no:
                    skipped += 1
                    continue

                order = Order.objects.filter(sn=int(order_no)).first()
                if not order:
                    skipped += 1
                    continue

                if hasattr(order, "sale") and order.sale is not None:
                    skipped += 1
                    continue

                sale = Sale(order=order)
                sale.bill_no = str(bill_no or "")
                if sale_date_bs:
                    sale.sale_date = str(sale_date_bs)
                sale.save()
                imported += 1

            messages.success(
                request,
                f"Imported {imported} sales, skipped {skipped} duplicate/invalid rows.",
            )
            return redirect("sales:sales_list")

        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Failed to import Excel: {exc}")
            return redirect("sales:import_excel")

    return render(request, "sales/import_excel.html")
