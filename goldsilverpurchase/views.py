from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import GoldSilverPurchase, Party, CustomerPurchase
from ornament.models import Ornament, MainCategory, SubCategory, Kaligar
from order.models import Order, OrderPayment, OrderOrnament
from sales.models import Sale
from django.db.models import Sum
import nepali_datetime as ndt
import openpyxl
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Q
from io import BytesIO
from django.contrib import messages
from decimal import Decimal
from .forms import CustomerPurchaseForm
from openpyxl import Workbook

def D(value):
    """Convert None, empty, float, int safely to Decimal."""
    if value is None or value == "":
        return Decimal("0.00")
    try:
        return Decimal(str(value))
    except:
        return Decimal("0.00")

class PurchaseListView(ListView):
    model = GoldSilverPurchase
    template_name = 'goldsilverpurchase/purchase_list.html'
    context_object_name = 'purchases'
    ordering = ['-bill_date', '-created_at']
    paginate_by = 10  # 20 purchases per page

    def get_queryset(self):
        queryset = super().get_queryset()
        date_str = self.request.GET.get('date')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        party_id = self.request.GET.get('party')
        metal_type=self.request.GET.get('metal_type')
        search = self.request.GET.get('search')

        if search:
            queryset = queryset.filter(
            Q(bill_no__icontains=search) |
            Q(party__party_name__icontains=search) |
            Q(metal_type__icontains=search) |
            Q(particular__icontains=search)
    )

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

        if metal_type:
            queryset = queryset.filter(metal_type=metal_type)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_quantity'] = self.get_queryset().aggregate(total=Sum('quantity'))['total'] or 0
        context['total_amount'] = self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0
        
        # Gold and Silver purchase totals (all-time)
        context['gold_purchase'] = (
            GoldSilverPurchase.objects.filter(metal_type__icontains="gold")
            .aggregate(total=Sum("quantity"))
            .get("total")
            or 0
        )
        context['silver_purchase'] = (
            GoldSilverPurchase.objects.filter(metal_type__icontains="silver")
            .aggregate(total=Sum("quantity"))
            .get("total")
            or 0
        )
        
        context['date'] = self.request.GET.get('date', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['parties'] = Party.objects.all()
        context['selected_party'] = self.request.GET.get('party', '')
        context['metal_type']=self.request.GET.get('metal_type')
        return context

class PartyCreateView(CreateView):
    model = Party
    fields = ['party_name', 'panno']
    template_name = 'goldsilverpurchase/party_form.html'
    success_url = reverse_lazy('gsp:purchaselist')


class PurchaseCreateView(CreateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party',
        'particular', 'metal_type', 'quantity',
        'rate', 'wages', 'discount','amount', 'payment_mode'
    ]
    template_name = 'goldsilverpurchase/purchase_form.html'
    success_url = reverse_lazy('gsp:purchaselist')


class PurchaseUpdateView(UpdateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party',
        'particular', 'metal_type', 'quantity',
        'rate', 'wages','discount', 'amount', 'payment_mode',
        'is_paid', 'remarks'
    ]
    template_name = 'goldsilverpurchase/purchase_form.html'
    success_url = reverse_lazy('gsp:purchaselist')


class PurchaseDeleteView(DeleteView):
    model = GoldSilverPurchase
    template_name = 'goldsilverpurchase/purchase_confirm_delete.html'
    success_url = reverse_lazy('gsp:purchaselist')


# ---------------------- Customer Purchases ----------------------
class CustomerPurchaseListView(ListView):
    model = CustomerPurchase
    template_name = 'goldsilverpurchase/customer_purchase_list.html'
    context_object_name = 'customer_purchases'
    ordering = ['-purchase_date', '-created_at']
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search')
        date_str = self.request.GET.get('date')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        metal_type = self.request.GET.get('metal_type')

        if search:
            qs = qs.filter(
                Q(sn__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(location__icontains=search) |
                Q(phone_no__icontains=search) |
                Q(ornament_name__icontains=search)
            )

        if date_str:
            try:
                y, m, d = map(int, date_str.split('-'))
                qs = qs.filter(purchase_date=ndt.date(y, m, d))
            except ValueError:
                pass
        elif start_date_str and end_date_str:
            try:
                y1, m1, d1 = map(int, start_date_str.split('-'))
                y2, m2, d2 = map(int, end_date_str.split('-'))
                qs = qs.filter(purchase_date__range=(ndt.date(y1, m1, d1), ndt.date(y2, m2, d2)))
            except ValueError:
                pass

        if metal_type:
            qs = qs.filter(metal_type=metal_type)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx['total_weight'] = qs.aggregate(total=Sum('weight'))['total'] or Decimal('0')
        ctx['total_refined_weight'] = qs.aggregate(total=Sum('refined_weight'))['total'] or Decimal('0')
        ctx['date'] = self.request.GET.get('date', '')
        ctx['start_date'] = self.request.GET.get('start_date', '')
        ctx['end_date'] = self.request.GET.get('end_date', '')
        ctx['search'] = self.request.GET.get('search', '')
        ctx['metal_type'] = self.request.GET.get('metal_type', '')
        return ctx


class CustomerPurchaseCreateView(CreateView):
    model = CustomerPurchase
    form_class = CustomerPurchaseForm
    template_name = 'goldsilverpurchase/customer_purchase_form.html'
    success_url = reverse_lazy('gsp:customer_purchase_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Create Customer Purchase'
        return ctx


class CustomerPurchaseUpdateView(UpdateView):
    model = CustomerPurchase
    form_class = CustomerPurchaseForm
    template_name = 'goldsilverpurchase/customer_purchase_form.html'
    success_url = reverse_lazy('gsp:customer_purchase_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Update Customer Purchase'
        return ctx


class CustomerPurchaseDeleteView(DeleteView):
    model = CustomerPurchase
    template_name = 'goldsilverpurchase/customer_purchase_confirm_delete.html'
    success_url = reverse_lazy('gsp:customer_purchase_list')



def print_view(request):
    view = PurchaseListView()
    view.request = request  # attach request
    purchases = view.get_queryset()

    total_amount = purchases.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, "goldsilverpurchase/print_view.html", {
        "purchases": purchases,
        "total_amount": total_amount
    })


def export_excel(request):
    view = PurchaseListView()
    view.request = request  # attach request
    purchases = view.get_queryset()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Purchases"

    headers = [
        "Bill No", "Bill Date (BS)", "Party Name","Pan No", "Metal",
        "Particular", "Qty", "Rate", "Wages", "Discount","Amount", "Payment","Paid", "Remarks"
    ]
    ws.append(headers)

    for p in purchases:
        ws.append([
            p.bill_no,
            str(p.bill_date),
            p.party.party_name,
            p.party.panno,
            p.metal_type,
            p.particular,
            p.quantity,
            p.rate,
            p.wages,
            p.discount,
            p.amount,
            p.payment_mode,
            p.is_paid,
            p.remarks
        ])

    # Auto column width
    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_length + 2

    # Create virtual file
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename="purchases.xlsx"'

    return response


def export_customer_excel(request):
    view = CustomerPurchaseListView()
    view.request = request
    purchases = view.get_queryset()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CustomerPurchases"

    headers = [
        "SN", "Purchase Date (BS)", "Customer Name", "Location", "Phone",
        "Metal", "Ornament Name", "Weight", "Refined Weight", "Rate", "Amount"
    ]
    ws.append(headers)

    for p in purchases:
        ws.append([
            p.sn,
            str(p.purchase_date),
            p.customer_name,
            p.location,
            p.phone_no,
            p.get_metal_type_display(),
            p.ornament_name,
            p.weight,
            p.refined_weight,
            p.rate,
            p.amount,
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
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename="customer_purchases.xlsx"'

    return response



def to_decimal(val):
    if val is None or val == "":
        return Decimal("0")
    return Decimal(str(val))   # SAFE conversion from float → Decimal


def import_excel(request):
    if request.method == "POST":
        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Please upload an Excel file.")
            return redirect("gsp:gsp_import_excel")

        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            imported = 0
            skipped = 0

            for row in ws.iter_rows(min_row=2, values_only=True):

                if not any(row):   # skip empty rows
                    continue

                try:
                    (
                        bill_no,
                        bill_date_bs,
                        party_name,
                        party_pan,
                        metal_type,
                        particular,
                        qty,
                        rate,
                        wages,
                        discount,
                        amount,
                        payment_mode,
                        is_paid,
                        remarks
                    ) = row
                except Exception:
                    messages.error(request, "Excel format is incorrect. Columns mismatch.")
                    return redirect("gsp:gsp_import_excel")

                # =============== 1️⃣ Duplicate Bill Check ===============
                if GoldSilverPurchase.objects.filter(bill_no=str(bill_no)).exists():
                    skipped += 1
                    continue

                # =============== 2️⃣ Find/Create Party ===============
                party = None

                if party_pan:
                    party = Party.objects.filter(panno=str(party_pan)).first()

                if not party:
                    party = Party.objects.create(
                        party_name=party_name or "Unknown",
                        panno=str(party_pan) if party_pan else "",
                    )

                # =============== 3️⃣ Convert BS Date ===============
                try:
                    y, m, d = map(int, str(bill_date_bs).split("-"))
                    bill_date = ndt.date(y, m, d)
                except:
                    bill_date = ndt.date.today()

                # =============== 4️⃣ Convert all decimals safely ===============
                qty = to_decimal(qty)
                rate = to_decimal(rate)
                wages = to_decimal(wages)
                amount = to_decimal(amount)
                discount=to_decimal(discount)

                # =============== 5️⃣ Create Purchase ===============
                GoldSilverPurchase.objects.create(
                    bill_no=str(bill_no),
                    bill_date=bill_date,
                    party=party,
                    metal_type=metal_type,
                    particular=particular,
                    quantity=qty,
                    rate=rate,
                    wages=wages,
                    amount = amount,
                    discount = discount,
                    payment_mode=payment_mode,
                    is_paid=bool(is_paid),
                    remarks=remarks
                )

                imported += 1

            messages.success(
                request,
                f"Imported: {imported} | Skipped duplicates: {skipped}"
            )
            return redirect("gsp:purchaselist")

        except Exception as e:
            messages.error(request, f"Error while importing: {e}")
            return redirect("gsp:gsp_import_excel")

    return render(request, "goldsilverpurchase/import_excel.html")


def import_customer_excel(request):
    if request.method == "POST":
        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Please upload an Excel file.")
            return redirect("gsp:customer_import_excel")

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
                        sn,
                        purchase_date_bs,
                        customer_name,
                        location,
                        phone_no,
                        metal_type,
                        ornament_name,
                        weight,
                        refined_weight,
                        rate,
                        amount,
                    ) = row
                except Exception:
                    messages.error(request, "Excel format is incorrect. Columns mismatch.")
                    return redirect("gsp:customer_import_excel")

                if CustomerPurchase.objects.filter(sn=str(sn)).exists():
                    skipped += 1
                    continue

                try:
                    y, m, d = map(int, str(purchase_date_bs).split("-"))
                    purchase_date = ndt.date(y, m, d)
                except Exception:
                    purchase_date = None

                metal_value = str(metal_type or CustomerPurchase.MetalType.GOLD).strip().lower()
                if metal_value not in [choice[0] for choice in CustomerPurchase.MetalType.choices]:
                    metal_value = CustomerPurchase.MetalType.GOLD

                CustomerPurchase.objects.create(
                    sn=str(sn),
                    purchase_date=purchase_date,
                    customer_name=customer_name or "",
                    location=location or "",
                    phone_no=phone_no or "",
                    metal_type=metal_value,
                    ornament_name=ornament_name or "",
                    weight=D(weight),
                    refined_weight=D(refined_weight),
                    rate=D(rate),
                    amount=D(amount),
                )
                imported += 1

            messages.success(
                request,
                f"Imported: {imported} | Skipped duplicates: {skipped}"
            )
            return redirect("gsp:customer_purchase_list")

        except Exception as e:
            messages.error(request, f"Error while importing: {e}")
            return redirect("gsp:customer_import_excel")

    return render(request, "goldsilverpurchase/customer_import_excel.html")


def data_settings(request):
    """Settings page with data export and import controls."""
    if request.method == "POST":
        if "import_file" in request.FILES:
            return import_all_data(request)
        elif "delete_all" in request.POST:
            return delete_all_data(request)
    return render(request, "goldsilverpurchase/data_settings.html")


def export_all_data(request):
    """Export all key datasets into a single Excel workbook with multiple sheets."""

    def as_float(val):
        try:
            return float(val)
        except Exception:
            return val

    def as_str_date(val):
        """Convert nepali_datetime.date or datetime to string."""
        if val is None:
            return ""
        return str(val)

    wb = Workbook()
    # Remove default sheet to control ordering
    default_ws = wb.active
    wb.remove(default_ws)

    def add_sheet(title, headers, rows):
        ws = wb.create_sheet(title=title[:31])
        ws.append(headers)
        for row in rows:
            ws.append(row)

    # Gold/Silver Purchases
    gsp_rows = [
        (
            p.bill_no,
            as_str_date(p.bill_date),
            p.party.party_name if p.party else "",
            p.particular,
            p.metal_type,
            as_float(p.quantity),
            as_float(p.rate),
            as_float(p.wages),
            as_float(p.discount),
            as_float(p.amount),
            p.payment_mode,
            p.is_paid,
            p.remarks,
            as_str_date(p.created_at),
            as_str_date(p.updated_at),
        )
        for p in GoldSilverPurchase.objects.select_related("party").order_by("created_at")
    ]
    add_sheet(
        "GoldSilverPurchase",
        [
            "Bill No",
            "Bill Date",
            "Party",
            "Particular",
            "Metal Type",
            "Quantity",
            "Rate",
            "Wages",
            "Discount",
            "Amount",
            "Payment Mode",
            "Is Paid",
            "Remarks",
            "Created At",
            "Updated At",
        ],
        gsp_rows,
    )

    # Customer Purchases
    customer_rows = [
        (
            cp.sn,
            as_str_date(cp.purchase_date),
            cp.customer_name,
            cp.location,
            cp.phone_no,
            cp.metal_type,
            cp.ornament_name,
            as_float(cp.weight),
            as_float(cp.refined_weight),
            as_float(cp.rate),
            as_float(cp.amount),
            as_str_date(cp.created_at),
            as_str_date(cp.updated_at),
        )
        for cp in CustomerPurchase.objects.order_by("created_at")
    ]
    add_sheet(
        "CustomerPurchase",
        [
            "SN",
            "Purchase Date",
            "Customer Name",
            "Location",
            "Phone",
            "Metal Type",
            "Ornament",
            "Weight",
            "Refined Weight",
            "Rate",
            "Amount",
            "Created At",
            "Updated At",
        ],
        customer_rows,
    )

    # Orders
    order_rows = [
        (
            o.sn,
            as_str_date(o.order_date),
            as_str_date(o.deliver_date),
            o.customer_name,
            o.phone_number,
            o.status,
            as_float(o.discount),
            as_float(o.amount),
            as_float(o.subtotal),
            as_float(o.tax),
            as_float(o.total),
            o.payment_mode,
            as_float(o.payment_amount),
            as_float(o.remaining_amount),
            as_str_date(o.created_at),
            as_str_date(o.updated_at),
        )
        for o in Order.objects.order_by("created_at")
    ]
    add_sheet(
        "Orders",
        [
            "SN",
            "Order Date",
            "Deliver Date",
            "Customer Name",
            "Phone",
            "Status",
            "Discount",
            "Amount",
            "Subtotal",
            "Tax",
            "Total",
            "Payment Mode",
            "Payment Amount",
            "Remaining Amount",
            "Created At",
            "Updated At",
        ],
        order_rows,
    )

    # Order Payments
    payment_rows = [
        (
            op.order_id,
            op.payment_mode,
            as_float(op.amount),
            as_str_date(op.created_at),
            as_str_date(op.updated_at),
        )
        for op in OrderPayment.objects.select_related("order").order_by("created_at")
    ]
    add_sheet(
        "OrderPayments",
        ["Order SN", "Payment Mode", "Amount", "Created At", "Updated At"],
        payment_rows,
    )

    # Order Ornaments
    order_ornament_rows = [
        (
            oo.order_id,
            oo.ornament_id,
            as_float(oo.gold_rate),
            as_float(oo.diamond_rate),
            as_float(oo.zircon_rate),
            as_float(oo.stone_rate),
            as_float(oo.jarti),
            as_float(oo.jyala),
            as_float(oo.line_amount),
            as_str_date(oo.created_at),
            as_str_date(oo.updated_at),
        )
        for oo in OrderOrnament.objects.select_related("order", "ornament").order_by("created_at")
    ]
    add_sheet(
        "OrderOrnaments",
        [
            "Order SN",
            "Ornament ID",
            "Gold Rate",
            "Diamond Rate",
            "Zircon Rate",
            "Stone Rate",
            "Jarti",
            "Jyala",
            "Line Amount",
            "Created At",
            "Updated At",
        ],
        order_ornament_rows,
    )

    # Ornaments
    ornament_rows = [
        (
            orn.id,
            orn.code,
            orn.ornament_name,
            orn.metal_type,
            orn.type,
            orn.ornament_type,
            orn.maincategory.name if orn.maincategory else "",
            orn.subcategory.name if orn.subcategory else "",
            orn.kaligar.name if orn.kaligar else "",
            as_float(orn.weight),
            as_float(orn.gross_weight),
            as_float(orn.diamond_weight),
            as_float(orn.zircon_weight),
            as_float(orn.stone_weight),
            as_float(orn.stone_totalprice),
            as_float(orn.jarti),
            as_float(orn.jyala),
            as_str_date(orn.ornament_date),
            orn.description or "",
            orn.image.url if orn.image else "",
            as_str_date(orn.created_at),
            as_str_date(orn.updated_at),
        )
        for orn in Ornament.objects.select_related("maincategory", "subcategory", "kaligar").order_by("created_at")
    ]
    add_sheet(
        "Ornaments",
        [
            "ID",
            "Code",
            "Name",
            "Metal Type",
            "Karat",
            "Ornament Type",
            "Main Category",
            "Sub Category",
            "Kaligar",
            "Weight",
            "Gross Weight",
            "Diamond Weight",
            "Zircon Weight",
            "Stone Weight",
            "Stone Total Price",
            "Jarti",
            "Jyala",
            "Ornament Date",
            "Description",
            "Image URL",
            "Created At",
            "Updated At",
        ],
        ornament_rows,
    )

    # Sales
    sale_rows = [
        (
            s.order_id,
            s.bill_no,
            as_str_date(s.sale_date),
            as_str_date(s.created_at),
            as_str_date(s.updated_at),
        )
        for s in Sale.objects.select_related("order").order_by("created_at")
    ]
    add_sheet(
        "Sales",
        ["Order SN", "Bill No", "Sale Date", "Created At", "Updated At"],
        sale_rows,
    )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=all_data.xlsx"
    wb.save(response)
    return response


def import_all_data(request):
    """Import all data from a multi-sheet Excel file."""
    if request.method != "POST" or "import_file" not in request.FILES:
        return redirect("gsp:data_settings")

    file = request.FILES.get("import_file")
    if not file:
        messages.error(request, "Please upload a file.")
        return redirect("gsp:data_settings")

    try:
        wb = openpyxl.load_workbook(file)
        imported_count = {}
        errors = []
        ornament_id_map = {}  # Map old ornament IDs to new ones

        def to_decimal(val):
            if val is None or val == "":
                return Decimal("0.00")
            try:
                return Decimal(str(val))
            except Exception:
                return Decimal("0.00")

        def to_date(val):
            """Convert string date in Y-M-D format to nepali date."""
            if not val:
                return None
            try:
                if isinstance(val, str):
                    y, m, d = map(int, val.split("-"))
                else:
                    return None
                return ndt.date(y, m, d)
            except Exception:
                return None

        # ========== Import GoldSilverPurchase ==========
        if "GoldSilverPurchase" in wb.sheetnames:
            ws = wb["GoldSilverPurchase"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                try:
                    (
                        bill_no,
                        bill_date,
                        party_name,
                        particular,
                        metal_type,
                        quantity,
                        rate,
                        wages,
                        discount,
                        amount,
                        payment_mode,
                        is_paid,
                        remarks,
                        created_at,
                        updated_at,
                    ) = row[:15]

                    if GoldSilverPurchase.objects.filter(bill_no=str(bill_no)).exists():
                        continue

                    party = None
                    if party_name:
                        party = Party.objects.filter(party_name=party_name).first()
                        if not party:
                            party = Party.objects.create(
                                party_name=party_name,
                                panno="000000000",  # Placeholder
                            )

                    GoldSilverPurchase.objects.create(
                        bill_no=str(bill_no),
                        bill_date=to_date(bill_date),
                        party=party,
                        particular=particular,
                        metal_type=metal_type or "gold",
                        quantity=to_decimal(quantity),
                        rate=to_decimal(rate),
                        wages=to_decimal(wages),
                        discount=to_decimal(discount),
                        amount=to_decimal(amount),
                        payment_mode=payment_mode or "cash",
                        is_paid=bool(is_paid),
                        remarks=remarks,
                    )
                    count += 1
                except Exception as e:
                    errors.append(f"GoldSilverPurchase row error: {e}")
            imported_count["GoldSilverPurchase"] = count

        # ========== Import CustomerPurchase ==========
        if "CustomerPurchase" in wb.sheetnames:
            ws = wb["CustomerPurchase"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                try:
                    (
                        sn,
                        purchase_date,
                        customer_name,
                        location,
                        phone_no,
                        metal_type,
                        ornament_name,
                        weight,
                        refined_weight,
                        rate,
                        amount,
                        created_at,
                        updated_at,
                    ) = row[:13]

                    if CustomerPurchase.objects.filter(sn=str(sn)).exists():
                        continue

                    CustomerPurchase.objects.create(
                        sn=str(sn),
                        purchase_date=to_date(purchase_date),
                        customer_name=customer_name or "",
                        location=location or "",
                        phone_no=phone_no or "",
                        metal_type=metal_type or "gold",
                        ornament_name=ornament_name or "",
                        weight=to_decimal(weight),
                        refined_weight=to_decimal(refined_weight),
                        rate=to_decimal(rate),
                        amount=to_decimal(amount),
                    )
                    count += 1
                except Exception as e:
                    errors.append(f"CustomerPurchase row error: {e}")
            imported_count["CustomerPurchase"] = count

        # ========== Import Orders ==========
        if "Orders" in wb.sheetnames:
            ws = wb["Orders"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                try:
                    (
                        sn,
                        order_date,
                        deliver_date,
                        customer_name,
                        phone_number,
                        status,
                        discount,
                        amount,
                        subtotal,
                        tax,
                        total,
                        payment_mode,
                        payment_amount,
                        remaining_amount,
                        created_at,
                        updated_at,
                    ) = row[:16]

                    if Order.objects.filter(sn=sn).exists():
                        continue

                    Order.objects.create(
                        sn=sn,
                        order_date=to_date(order_date),
                        deliver_date=to_date(deliver_date),
                        customer_name=customer_name or "",
                        phone_number=phone_number or "0000000000",
                        status=status or "order",
                        discount=to_decimal(discount),
                        amount=to_decimal(amount),
                        subtotal=to_decimal(subtotal),
                        tax=to_decimal(tax),
                        total=to_decimal(total),
                        payment_mode=payment_mode or "cash",
                        payment_amount=to_decimal(payment_amount),
                        remaining_amount=to_decimal(remaining_amount),
                    )
                    count += 1
                except Exception as e:
                    errors.append(f"Orders row error: {e}")
            imported_count["Orders"] = count

        # ========== Import OrderPayments ==========
        if "OrderPayments" in wb.sheetnames:
            ws = wb["OrderPayments"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                try:
                    (
                        order_sn,
                        payment_mode,
                        amount,
                        created_at,
                        updated_at,
                    ) = row[:5]

                    try:
                        order = Order.objects.get(sn=order_sn)
                        OrderPayment.objects.create(
                            order=order,
                            payment_mode=payment_mode or "cash",
                            amount=to_decimal(amount),
                        )
                        count += 1
                    except Order.DoesNotExist:
                        pass
                except Exception as e:
                    errors.append(f"OrderPayments row error: {e}")
            imported_count["OrderPayments"] = count

        # ========== Import Ornaments ==========
        if "Ornaments" in wb.sheetnames:
            ws = wb["Ornaments"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                try:
                    (
                        orn_id,
                        code,
                        ornament_name,
                        metal_type,
                        karat,
                        ornament_type,
                        main_category,
                        sub_category,
                        kaligar_name,
                        weight,
                        gross_weight,
                        diamond_weight,
                        zircon_weight,
                        stone_weight,
                        stone_total_price,
                        jarti,
                        jyala,
                        ornament_date,
                        description,
                        image_url,
                        created_at,
                        updated_at,
                    ) = row[:23]

                    # Convert ornament ID to integer for consistent mapping
                    orn_id = int(orn_id) if orn_id else None

                    # Skip if ornament with same code already exists, but still map the ID
                    if code:
                        existing = Ornament.objects.filter(code=str(code)).first()
                        if existing:
                            # Map old ID to existing ornament
                            ornament_id_map[orn_id] = existing.id
                            continue

                    # Get or create categories
                    main_cat = None
                    if main_category:
                        main_cat, _ = MainCategory.objects.get_or_create(
                            name=main_category
                        )

                    sub_cat = None
                    if sub_category:
                        sub_cat, _ = SubCategory.objects.get_or_create(
                            name=sub_category
                        )

                    # Get or create kaligar by name
                    kaligar = None
                    if kaligar_name:
                        kaligar, _ = Kaligar.objects.get_or_create(
                            name=kaligar_name,
                            defaults={"panno": "000000000"}
                        )
                    else:
                        # Fallback to first kaligar or create default
                        kaligar = Kaligar.objects.first()
                        if not kaligar:
                            kaligar = Kaligar.objects.create(
                                name="Default",
                                panno="000000000",
                            )

                    new_ornament = Ornament.objects.create(
                        code=str(code) if code else None,
                        ornament_name=ornament_name or "",
                        metal_type=metal_type or "Gold",
                        type=karat or "24KARAT",
                        ornament_type=ornament_type or "stock",
                        maincategory=main_cat,
                        subcategory=sub_cat,
                        kaligar=kaligar,
                        weight=to_decimal(weight),
                        gross_weight=to_decimal(gross_weight),
                        diamond_weight=to_decimal(diamond_weight),
                        zircon_weight=to_decimal(zircon_weight),
                        stone_weight=to_decimal(stone_weight),
                        stone_totalprice=to_decimal(stone_total_price),
                        jarti=to_decimal(jarti),
                        jyala=to_decimal(jyala),
                        ornament_date=to_date(ornament_date),
                        description=description or "",
                    )
                    # Map old ID to new ID
                    ornament_id_map[orn_id] = new_ornament.id
                    count += 1
                except Exception as e:
                    errors.append(f"Ornaments row error: {e}")
            imported_count["Ornaments"] = count

        # ========== Import OrderOrnaments ==========
        if "OrderOrnaments" in wb.sheetnames:
            ws = wb["OrderOrnaments"]
            count = 0
            row_num = 1
            for row in ws.iter_rows(min_row=2, values_only=True):
                row_num += 1
                if not any(row):
                    continue
                try:
                    (
                        order_sn,
                        ornament_id,
                        gold_rate,
                        diamond_rate,
                        zircon_rate,
                        stone_rate,
                        jarti,
                        jyala,
                        line_amount,
                        created_at,
                        updated_at,
                    ) = row[:11]

                    try:
                        order = Order.objects.get(sn=order_sn)
                        # Convert ornament_id to integer for map lookup
                        ornament_id = int(ornament_id) if ornament_id else None
                        # Use mapped ornament ID from import
                        mapped_ornament_id = ornament_id_map.get(ornament_id)
                        if mapped_ornament_id:
                            ornament = Ornament.objects.get(id=mapped_ornament_id)
                            OrderOrnament.objects.create(
                                order=order,
                                ornament=ornament,
                                gold_rate=to_decimal(gold_rate),
                                diamond_rate=to_decimal(diamond_rate),
                                zircon_rate=to_decimal(zircon_rate),
                                stone_rate=to_decimal(stone_rate),
                                jarti=to_decimal(jarti),
                                jyala=to_decimal(jyala),
                                line_amount=to_decimal(line_amount),
                            )
                            count += 1
                        else:
                            errors.append(f"OrderOrnaments row {row_num}: Ornament ID {ornament_id} not found in mapping")
                    except Order.DoesNotExist:
                        errors.append(f"OrderOrnaments row {row_num}: Order SN {order_sn} not found")
                    except Ornament.DoesNotExist:
                        errors.append(f"OrderOrnaments row {row_num}: Ornament ID {mapped_ornament_id} not found after mapping")
                except Exception as e:
                    errors.append(f"OrderOrnaments row error: {e}")
            imported_count["OrderOrnaments"] = count

        # ========== Import Sales ==========
        if "Sales" in wb.sheetnames:
            ws = wb["Sales"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                try:
                    (
                        order_sn,
                        bill_no,
                        sale_date,
                        created_at,
                        updated_at,
                    ) = row[:5]

                    try:
                        order = Order.objects.get(sn=order_sn)
                        if not Sale.objects.filter(order=order).exists():
                            Sale.objects.create(
                                order=order,
                                bill_no=bill_no or None,
                                sale_date=to_date(sale_date),
                            )
                            count += 1
                    except Order.DoesNotExist:
                        pass
                except Exception as e:
                    errors.append(f"Sales row error: {e}")
            imported_count["Sales"] = count

        # Prepare summary message
        summary_msg = "Import completed: " + " | ".join(
            [f"{k}: {v}" for k, v in imported_count.items() if v > 0]
        )
        summary_msg += f" | Ornament ID mappings: {len(ornament_id_map)}"
        messages.success(request, summary_msg)

        if errors:
            error_summary = f"{len(errors)} row(s) had errors:\n" + "\n".join(errors[:20])
            if len(errors) > 20:
                error_summary += f"\n... and {len(errors) - 20} more errors"
            messages.warning(request, error_summary)
            import logging
            logger = logging.getLogger(__name__)
            for error in errors:
                logger.error(error)

        return redirect("gsp:data_settings")

    except Exception as e:
        messages.error(request, f"Import failed: {str(e)}")
        return redirect("gsp:data_settings")


def delete_all_data(request):
    """Delete all data from primary tables (with confirmation)."""
    if request.method != "POST":
        return redirect("gsp:data_settings")

    # Verify confirmation token to prevent accidental deletion
    confirm_token = request.POST.get("confirm_delete")
    if confirm_token != "DELETE_ALL_DATA_CONFIRMED":
        messages.error(request, "Deletion not confirmed. Data was not deleted.")
        return redirect("gsp:data_settings")

    try:
        # Delete in order of dependencies (children first)
        order_payment_count = OrderPayment.objects.count()
        order_ornament_count = OrderOrnament.objects.count()
        sales_count = Sale.objects.count()
        order_count = Order.objects.count()
        ornament_count = Ornament.objects.count()
        customer_purchase_count = CustomerPurchase.objects.count()
        gsp_count = GoldSilverPurchase.objects.count()

        # Delete related records first
        OrderPayment.objects.all().delete()
        OrderOrnament.objects.all().delete()
        Sale.objects.all().delete()
        Order.objects.all().delete()
        Ornament.objects.all().delete()
        CustomerPurchase.objects.all().delete()
        GoldSilverPurchase.objects.all().delete()

        total_deleted = (
            order_payment_count
            + order_ornament_count
            + sales_count
            + order_count
            + ornament_count
            + customer_purchase_count
            + gsp_count
        )

        messages.success(
            request,
            f"All data deleted successfully. Total records removed: {total_deleted}",
        )
    except Exception as e:
        messages.error(request, f"Error deleting data: {str(e)}")

    return redirect("gsp:data_settings")
