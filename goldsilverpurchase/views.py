from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db import models
from django.db.models import Sum, Q, F, IntegerField, Avg
from django.db.models.functions import Cast
from .models import GoldSilverPurchase, Party, CustomerPurchase, MetalStock, MetalStockType, MetalStockMovement
from ornament.models import Ornament, MainCategory, SubCategory, Kaligar
from order.models import Order, OrderPayment, OrderOrnament
from sales.models import Sale
import nepali_datetime as ndt
import openpyxl
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from django.shortcuts import render, redirect
from io import BytesIO
from django.contrib import messages
from decimal import Decimal
from .forms import CustomerPurchaseForm, MetalStockForm
from openpyxl import Workbook
from .forms_movement import MetalStockMovementForm
from datetime import date, datetime

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
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import openpyxl
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def export_metalstock_xlsx(request):
    wb = openpyxl.Workbook()
    ws_stock = wb.active
    ws_stock.title = 'MetalStock'
    ws_movement = wb.create_sheet(title='MetalStockMovement')

    # MetalStock sheet
    stock_headers = [
        'StockID', 'MetalType', 'StockType', 'Purity', 'Quantity', 'UnitCost', 'RateUnit', 'TotalCost', 'Location', 'Remarks', 'CreatedAt', 'LastUpdated'
    ]
    ws_stock.append(stock_headers)
    for stock in MetalStock.objects.all():
        ws_stock.append([
            stock.id,
            stock.metal_type,
            stock.stock_type.name if stock.stock_type else '',
            stock.purity,
            float(stock.quantity) if stock.quantity is not None else '',
            float(stock.unit_cost) if stock.unit_cost is not None else '',
            stock.rate_unit,
            float(stock.total_cost) if stock.total_cost is not None else '',
            stock.location or '',
            stock.remarks or '',
            str(stock.created_at) if stock.created_at else '',
            str(stock.last_updated) if stock.last_updated else ''
        ])

    # MetalStockMovement sheet
    movement_headers = [
        'MovementID', 'MetalStockID', 'MovementType', 'Quantity', 'Rate', 'ReferenceType', 'ReferenceID', 'Notes', 'MovementDate', 'CreatedAt'
    ]
    ws_movement.append(movement_headers)
    for m in MetalStockMovement.objects.all():
        ws_movement.append([
            m.id,
            m.metal_stock.id if m.metal_stock else '',
            m.movement_type,
            float(m.quantity) if m.quantity is not None else '',
            float(m.rate) if m.rate is not None else '',
            m.reference_type or '',
            m.reference_id or '',
            m.notes or '',
            str(m.movement_date) if m.movement_date else '',
            str(m.created_at) if m.created_at else ''
        ])

    # Auto-size columns for both sheets
    for ws in [ws_stock, ws_movement]:
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[column].width = max_length + 2

    from io import BytesIO
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=metalstock_export.xlsx'
    wb.save(response)
    return response

@method_decorator(csrf_exempt, name='dispatch')
class ImportMetalStockXLSXView(View):
    def post(self, request):
        from datetime import date, datetime
        file = request.FILES.get('file')
        if not file:
            return HttpResponse('No file uploaded.', status=400)
        wb = openpyxl.load_workbook(file)
        from decimal import Decimal
        from django.utils.dateparse import parse_date
        # --- Import MetalStock sheet ---
        ws_stock = wb['MetalStock'] if 'MetalStock' in wb.sheetnames else wb.active
        stock_rows = list(ws_stock.iter_rows(min_row=2, values_only=True))
        stock_objs = {}
        errors = []
        for idx, row in enumerate(stock_rows, start=2):
            try:
                stock_id, metal_type, stock_type_name, purity, quantity, unit_cost, rate_unit, total_cost, location, remarks, created_at, last_updated = row
                stock_type = MetalStockType.objects.filter(name=stock_type_name).first() if stock_type_name else None
                stock, _ = MetalStock.objects.update_or_create(
                    id=stock_id,
                    defaults={
                        'metal_type': metal_type or '',
                        'stock_type': stock_type,
                        'purity': purity or '',
                        'quantity': Decimal(quantity or 0),
                        'unit_cost': Decimal(unit_cost or 0),
                        'rate_unit': rate_unit or '',
                        'total_cost': Decimal(total_cost or 0),
                        'location': location or '',
                        'remarks': remarks or '',
                    }
                )
                stock_objs[stock_id] = stock
            except Exception as e:
                errors.append(f"Stock Row {idx}: {str(e)}")
        # --- Import MetalStockMovement sheet ---
        if 'MetalStockMovement' in wb.sheetnames:
            ws_movement = wb['MetalStockMovement']
            movement_rows = list(ws_movement.iter_rows(min_row=2, values_only=True))
            for idx, row in enumerate(movement_rows, start=2):
                try:
                    movement_id, metal_stock_id, movement_type, quantity, rate, reference_type, reference_id, notes, movement_date, created_at = row
                    stock = stock_objs.get(metal_stock_id) or MetalStock.objects.filter(id=metal_stock_id).first()
                    if not stock:
                        errors.append(f"Movement Row {idx}: MetalStockID {metal_stock_id} not found.")
                        continue
                    MetalStockMovement.objects.update_or_create(
                        id=movement_id,
                        defaults={
                            'metal_stock': stock,
                            'movement_type': movement_type or '',
                            'quantity': Decimal(quantity or 0),
                            'rate': Decimal(rate or 0),
                            'reference_type': reference_type or '',
                            'reference_id': reference_id or '',
                            'notes': notes or '',
                            'movement_date': parse_date(movement_date) if isinstance(movement_date, str) and movement_date else movement_date if isinstance(movement_date, (date, datetime)) else None,
                        }
                    )
                except Exception as e:
                    errors.append(f"Movement Row {idx}: {str(e)}")
        if errors:
            return HttpResponse('Import completed with errors:\n' + '\n'.join(errors), status=400)
        return HttpResponse('Import completed.')
class PurchaseCreateView(CreateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party',
        'particular', 'metal_type', 'purity', 'quantity',
        'rate', 'rate_unit', 'wages', 'discount','amount', 'payment_mode'
    ]
    template_name = 'goldsilverpurchase/purchase_form.html'
    success_url = reverse_lazy('gsp:purchaselist')


class PurchaseUpdateView(UpdateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party',
        'particular', 'metal_type', 'purity', 'quantity',
        'rate', 'rate_unit', 'wages','discount', 'amount', 'payment_mode',
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

        # Order by SN in descending numeric order
        qs = qs.annotate(sn_numeric=Cast('sn', IntegerField())).order_by('-sn_numeric')
        
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx['total_weight'] = qs.aggregate(total=Sum('weight'))['total'] or Decimal('0')
        ctx['total_refined_weight'] = qs.aggregate(total=Sum('refined_weight'))['total'] or Decimal('0')
        ctx['total_final_weight'] = qs.aggregate(total=Sum('final_weight'))['total'] or Decimal('0')
        ctx['total_profit_weight'] = qs.aggregate(total=Sum('profit_weight'))['total'] or Decimal('0')
        ctx['total_amount'] = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        ctx['total_profit'] = qs.aggregate(total=Sum('profit'))['total'] or Decimal('0')
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
        "Bill No", "Bill Date (BS)", "Party Name","Pan No", "Metal", "Purity",
        "Particular", "Qty", "Rate", "Rate Unit", "Wages", "Discount","Amount", "Payment","Paid", "Remarks"
    ]
    ws.append(headers)

    for p in purchases:
        ws.append([
            p.bill_no,
            str(p.bill_date),
            p.party.party_name,
            p.party.panno,
            p.metal_type,
            p.purity,
            p.particular,
            p.quantity,
            p.rate,
            p.rate_unit,
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
        "Purchase Date (BS)", "Customer Name", "Location", "Phone",
        "Metal", "Ornament Name", "Weight (तोल)", "Percentage", "Final Weight (तोल)", "Refined Weight (तोल)", "Rate (Per तोल)", "Amount"
    ]
    ws.append(headers)

    for p in purchases:
        ws.append([
            str(p.purchase_date),
            p.customer_name,
            p.location,
            p.phone_no,
            p.get_metal_type_display(),
            p.ornament_name,
            p.weight,
            p.percentage,
            p.final_weight,
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
                        purity,
                        particular,
                        qty,
                        rate,
                        rate_unit,
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
                purchase = GoldSilverPurchase.objects.create(
                    bill_no=str(bill_no),
                    bill_date=bill_date,
                    party=party,
                    metal_type=metal_type,
                    purity=purity or '24K',
                    particular=particular,
                    quantity=qty,
                    rate=rate,
                    rate_unit=rate_unit or 'tola',
                    wages=wages,
                    amount=amount,
                    discount=discount,
                    payment_mode=payment_mode,
                    is_paid=bool(is_paid),
                    remarks=remarks
                )

                # --- MetalStock logic ---
                # Determine stock_type: 'raw' if 'raw' in particular, else error
                stock_type_name = 'raw' if particular and 'raw' in particular.lower() else None
                if not stock_type_name:
                    messages.error(request, f"Purchase {purchase.bill_no}: Only 'raw' gold is supported for stock. Add 'raw' in particular.")
                    continue
                stock_type = MetalStockType.objects.filter(name=stock_type_name).first()
                if not stock_type:
                    stock_type = MetalStockType.objects.create(name=stock_type_name)
                # Always create MetalStock if not exists for metal_type, purity, and stock_type
                metal_stock, created = MetalStock.objects.get_or_create(
                    metal_type=metal_type,
                    purity=purity or '24K',
                    stock_type=stock_type,
                    defaults={
                        'quantity': 0,
                        'unit_cost': 0,
                        'rate_unit': rate_unit or 'tola',
                    }
                )
                # If it exists, ensure rate_unit is set (for legacy rows)
                if not created and not metal_stock.rate_unit:
                    metal_stock.rate_unit = rate_unit or 'tola'
                    metal_stock.save()
                # --- MetalStockMovement logic ---
                MetalStockMovement.objects.create(
                    metal_stock=metal_stock,
                    movement_type='in',
                    quantity=qty,
                    rate=rate,
                    reference_type='GoldSilverPurchase',
                    reference_id=purchase.bill_no,
                    notes=remarks,
                    movement_date=bill_date
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
                        purchase_date_bs,
                        customer_name,
                        location,
                        phone_no,
                        metal_type,
                        ornament_name,
                        weight,
                        percentage,
                        final_weight,
                        refined_weight,
                        rate,
                        amount,
                    ) = row
                except Exception:
                    messages.error(request, "Excel format is incorrect. Columns mismatch.")
                    return redirect("gsp:customer_import_excel")

                try:
                    y, m, d = map(int, str(purchase_date_bs).split("-"))
                    purchase_date = ndt.date(y, m, d)
                except Exception:
                    purchase_date = None

                metal_value = str(metal_type or CustomerPurchase.MetalType.GOLD).strip().lower()
                if metal_value not in [choice[0] for choice in CustomerPurchase.MetalType.choices]:
                    metal_value = CustomerPurchase.MetalType.GOLD

                CustomerPurchase.objects.create(
                    purchase_date=purchase_date,
                    customer_name=customer_name or "",
                    location=location or "",
                    phone_no=phone_no or "",
                    metal_type=metal_value,
                    ornament_name=ornament_name or "",
                    weight=D(weight),
                    percentage=D(percentage),
                    final_weight=D(final_weight),
                    refined_weight=D(refined_weight),
                    rate=D(rate),
                    amount=D(amount),
                )
                imported += 1

            messages.success(
                request,
                f"Imported: {imported} records"
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
        elif "delete_customer_purchases" in request.POST:
            return delete_customer_purchases(request)
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
            p.purity,
            as_float(p.quantity),
            as_float(p.rate),
            p.rate_unit,
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
            "Purity",
            "Quantity",
            "Rate",
            "Rate Unit",
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
            "Weight (Tola)",
            "Refined Weight (Tola)",
            "Rate (Per Tola)",
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
            o.order_type,
            o.description or "",
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
            "Order Type",
            "Description",
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
                        purity,
                        quantity,
                        rate,
                        rate_unit,
                        wages,
                        discount,
                        amount,
                        payment_mode,
                        is_paid,
                        remarks,
                        created_at,
                        updated_at,
                    ) = row[:17]

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
                        purity=purity or "22K",
                        quantity=to_decimal(quantity),
                        rate=to_decimal(rate),
                        rate_unit=rate_unit or "tola",
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
                        phone_no=phone_no or "0000000000",
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
                        order_type,
                        description,
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
                    ) = row[:18]

                    if Order.objects.filter(sn=sn).exists():
                        continue

                    Order.objects.create(
                        sn=sn,
                        order_date=to_date(order_date),
                        deliver_date=to_date(deliver_date),
                        customer_name=customer_name or "",
                        phone_number=phone_number or "0000000000",
                        status=status or "order",
                        order_type=order_type or "custom",
                        description=description or "",
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
                    ) = row[:22]

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


def delete_customer_purchases(request):
    """Delete all customer purchases with password protection."""
    if request.method != "POST":
        return redirect("gsp:data_settings")

    # Verify password
    password = request.POST.get("customer_purchase_password", "")
    confirm_text = request.POST.get("confirm_customer_delete", "")

    # Password for deleting customer purchases (set to "admin123" - can be changed)
    DELETE_PASSWORD = "admin123"

    if password != DELETE_PASSWORD:
        messages.error(request, "Incorrect password. Customer purchases were not deleted.")
        return redirect("gsp:data_settings")

    if confirm_text != "DELETE_CUSTOMER_PURCHASES":
        messages.error(request, "Confirmation text does not match. Customer purchases were not deleted.")
        return redirect("gsp:data_settings")

    try:
        customer_purchase_count = CustomerPurchase.objects.count()
        CustomerPurchase.objects.all().delete()

        messages.success(
            request,
            f"Successfully deleted {customer_purchase_count} customer purchases. This action cannot be undone."
        )
        return redirect("gsp:customer_purchase_list")

    except Exception as e:
        messages.error(request, f"Error while deleting customer purchases: {e}")
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

class MetalStockListView(ListView):
    """View to display all metal stocks (raw and refined)"""
    model = MetalStock
    template_name = 'goldsilverpurchase/metalstock_list.html'
    context_object_name = 'metal_stocks'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-last_updated', '-created_at')
        
        # Filter by metal type
        metal_type = self.request.GET.get('metal_type')
        if metal_type:
            queryset = queryset.filter(metal_type=metal_type)
        
        # Filter by stock type (raw/refined)
        stock_type = self.request.GET.get('stock_type')
        if stock_type:
            queryset = queryset.filter(stock_type__name=stock_type)
        
        # Filter by purity
        purity = self.request.GET.get('purity')
        if purity:
            queryset = queryset.filter(purity=purity)
        
        # Search by location
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(location__icontains=search) |
                Q(remarks__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the filtered base queryset
        filtered_queryset = self.get_queryset()
        
        # Summary statistics (always use unfiltered totals for dashboard)
        context['total_gold_quantity'] = (
            MetalStock.objects.filter(metal_type='gold')
            .aggregate(total=Sum('quantity'))['total'] or Decimal('0.000')
        )
        context['total_silver_quantity'] = (
            MetalStock.objects.filter(metal_type='silver')
            .aggregate(total=Sum('quantity'))['total'] or Decimal('0.000')
        )
        context['total_platinum_quantity'] = (
            MetalStock.objects.filter(metal_type='platinum')
            .aggregate(total=Sum('quantity'))['total'] or Decimal('0.000')
        )
        
        # Total value
        gold_value = MetalStock.objects.filter(metal_type='gold').aggregate(
            total=Sum(models.F('quantity') * models.F('unit_cost'), output_field=models.DecimalField())
        )['total'] or Decimal('0.00')
        
        silver_value = MetalStock.objects.filter(metal_type='silver').aggregate(
            total=Sum(models.F('quantity') * models.F('unit_cost'), output_field=models.DecimalField())
        )['total'] or Decimal('0.00')
        
        context['total_gold_value'] = gold_value
        context['total_silver_value'] = silver_value
        context['total_value'] = gold_value + silver_value
        
        # Breakdown by stock type
        context['raw_stocks'] = MetalStock.objects.filter(
            stock_type__name='raw'
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0.000')
        
        context['refined_stocks'] = MetalStock.objects.filter(
            stock_type__name='refined'
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0.000')
        
        # Low stock alerts (from filtered queryset)
        context['low_stock_items'] = [
            item for item in filtered_queryset if item.is_low_stock
        ]
        
        # Split filtered queryset into gold and silver for tabs
        gold_stocks = filtered_queryset.filter(metal_type='gold')
        silver_stocks = filtered_queryset.filter(metal_type='silver')
        
        context['gold_stocks'] = gold_stocks
        context['silver_stocks'] = silver_stocks
        
        # Average unit cost rates from MetalStock (weighted by quantity)
        # 1 tola = 11.6643 grams
        TOLA_TO_GRAM = Decimal('11.6643')
        
        # Function to calculate weighted average cost in tola
        def calculate_weighted_average_cost(stock_qs):
            """Calculate quantity-weighted average unit cost in per-tola"""
            total_value_per_gram = Decimal('0.00')
            total_quantity = Decimal('0.00')
            
            for stock in stock_qs:
                # Skip if no cost or quantity
                if not stock.unit_cost or not stock.quantity:
                    continue
                    
                # Convert unit cost to per-gram based on rate_unit
                if stock.rate_unit == 'gram':
                    per_gram = stock.unit_cost
                elif stock.rate_unit == '10gram':
                    per_gram = stock.unit_cost / Decimal('10')
                elif stock.rate_unit == 'tola':
                    per_gram = stock.unit_cost / TOLA_TO_GRAM
                else:
                    continue
                
                # Accumulate: (cost_per_gram × quantity)
                total_value_per_gram += per_gram * stock.quantity
                total_quantity += stock.quantity
            
            if total_quantity == 0:
                return Decimal('0.00')
            
            # Weighted average per-gram = total_value / total_quantity
            avg_per_gram = total_value_per_gram / total_quantity
            # Convert per-gram to per-tola
            avg_per_tola = avg_per_gram * TOLA_TO_GRAM
            return avg_per_tola
        
        gold_avg_rate_tola = calculate_weighted_average_cost(gold_stocks)
        silver_avg_rate_tola = calculate_weighted_average_cost(silver_stocks)
        
        context['avg_gold_purchase_rate_tola'] = gold_avg_rate_tola
        context['avg_silver_purchase_rate_tola'] = silver_avg_rate_tola
        
        return context


def metal_stock_detail(request, pk):
    """View stock details and its movement history"""
    # Always re-fetch the MetalStock from the DB to get the latest quantity
    from django.db.models import Sum
    metal_stock = MetalStock.objects.get(pk=pk)
    # Recalculate quantity from all movements (defensive, in case of any desync)
    total_in = metal_stock.movements.filter(movement_type='in').aggregate(total=Sum('quantity'))['total'] or 0
    total_out = metal_stock.movements.filter(movement_type='out').aggregate(total=Sum('quantity'))['total'] or 0
    total_adj = metal_stock.movements.filter(movement_type='adjustment').aggregate(total=Sum('quantity'))['total'] or 0
    metal_stock.quantity = total_in - total_out + total_adj
    metal_stock.save()
    movements = MetalStockMovement.objects.filter(metal_stock=metal_stock).order_by('-movement_date')
    # Calculate average unit cost from 'in' movements
    in_movements = movements.filter(movement_type='in')
    total_qty = 0
    total_cost = 0
    for m in in_movements:
        if m.rate and m.quantity:
            total_qty += float(m.quantity)
            total_cost += float(m.rate) * float(m.quantity)
    avg_unit_cost = (total_cost / total_qty) if total_qty else 0
    context = {
        'metal_stock': metal_stock,
        'movements': movements,
        'avg_unit_cost_from_movements': avg_unit_cost,
    }
    return render(request, 'goldsilverpurchase/metalstock_detail.html', context)


class MetalStockCreateView(CreateView):
    """Create a new metal stock"""
    model = MetalStock
    form_class = MetalStockForm
    template_name = 'goldsilverpurchase/metalstock_form.html'
    success_url = reverse_lazy('gsp:metal_stock_list')

    def form_valid(self, form):
        # Always save MetalStock first to get a primary key
        self.object = form.save(commit=False)
        self.object.save()  # Ensure PK exists
        add_quantity = form.cleaned_data.get('add_quantity')
        movement_notes = form.cleaned_data.get('movement_notes')
        if add_quantity not in (None, '') and add_quantity > 0:
            # Update quantity and save again
            self.object.quantity += add_quantity
            self.object.save()
            MetalStockMovement.objects.create(
                metal_stock=self.object,
                movement_type='in',
                quantity=add_quantity,
                rate=self.object.unit_cost,
                reference_type='Manual',
                reference_id=None,
                notes=movement_notes or 'Initial stock added on creation.'
            )
        messages.success(self.request, f"Metal stock for {form.cleaned_data['metal_type']} created successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Metal Stock'
        context['button_text'] = 'Create Stock'
        return context


class MetalStockUpdateView(UpdateView):
    """Update an existing metal stock"""
    model = MetalStock
    form_class = MetalStockForm
    template_name = 'goldsilverpurchase/metalstock_form.html'
    success_url = reverse_lazy('gsp:metal_stock_list')

    def form_valid(self, form):
        messages.success(self.request, f"Metal stock updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Metal Stock'
        context['button_text'] = 'Update Stock'
        return context


class MetalStockDeleteView(DeleteView):
    """Delete a metal stock"""
    model = MetalStock
    template_name = 'goldsilverpurchase/metalstock_confirm_delete.html'
    success_url = reverse_lazy('gsp:metal_stock_list')

    def delete(self, request, *args, **kwargs):
        metal_stock = self.get_object()
        metal_type = metal_stock.get_metal_type_display()
        messages.success(request, f"Metal stock for {metal_type} has been deleted successfully!")
        return super().delete(request, *args, **kwargs)

from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import MetalStockMovement
from .forms import MetalStockForm

class MetalStockMovementCreateView(CreateView):
    model = MetalStockMovement
    form_class = MetalStockMovementForm
    template_name = 'goldsilverpurchase/metalstockmovement_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.metal_stock = MetalStock.objects.get(pk=kwargs['stock_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.metal_stock = self.metal_stock
        response = super().form_valid(form)
        # Update MetalStock quantity
        if form.instance.movement_type == 'in':
            self.metal_stock.quantity += form.instance.quantity
        elif form.instance.movement_type == 'out':
            self.metal_stock.quantity -= form.instance.quantity
        self.metal_stock.save()
        return response

    def get_success_url(self):
        return reverse('gsp:metal_stock_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['metal_stock'] = self.metal_stock
        return context


class MetalStockMovementUpdateView(UpdateView):
    model = MetalStockMovement
    form_class = MetalStockMovementForm
    template_name = 'goldsilverpurchase/metalstockmovement_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        # After saving, recalculate the stock quantity from all movements
        metal_stock = self.object.metal_stock
        total_in = metal_stock.movements.filter(movement_type='in').aggregate(total=Sum('quantity'))['total'] or 0
        total_out = metal_stock.movements.filter(movement_type='out').aggregate(total=Sum('quantity'))['total'] or 0
        total_adj = metal_stock.movements.filter(movement_type='adjustment').aggregate(total=Sum('quantity'))['total'] or 0
        metal_stock.quantity = total_in - total_out + total_adj
        metal_stock.save()
        return response

    def get_success_url(self):
        return reverse('gsp:metal_stock_detail', kwargs={'pk': self.object.metal_stock_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['metal_stock'] = self.object.metal_stock
        context['is_edit'] = True
        return context


class MetalStockMovementDeleteView(DeleteView):
    model = MetalStockMovement
    template_name = 'goldsilverpurchase/metalstockmovement_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        metal_stock_id = self.object.metal_stock_id
        response = super().delete(request, *args, **kwargs)
        # After deletion, recalculate the stock quantity from all remaining movements
        from .models import MetalStock
        from django.db.models import Sum
        metal_stock = MetalStock.objects.get(pk=metal_stock_id)
        metal_stock_id = self.get_object().metal_stock_id
        response = super().delete(request, *args, **kwargs)
        from .models import MetalStock
        from django.db.models import Sum
        metal_stock = MetalStock.objects.get(pk=metal_stock_id)
        movements = metal_stock.movements.all()
        if not movements.exists():
            metal_stock.quantity = 0
        else:
            total_in = movements.filter(movement_type='in').aggregate(total=Sum('quantity'))['total'] or 0
            total_out = movements.filter(movement_type='out').aggregate(total=Sum('quantity'))['total'] or 0
            total_adj = movements.filter(movement_type='adjustment').aggregate(total=Sum('quantity'))['total'] or 0
            metal_stock.quantity = total_in - total_out + total_adj
        metal_stock.save()
        from django.urls import reverse
        return redirect(reverse('gsp:metal_stock_detail', kwargs={'pk': metal_stock_id}))

    def get_success_url(self):
        return reverse('gsp:metal_stock_detail', kwargs={'pk': self.object.metal_stock_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['metal_stock'] = self.object.metal_stock
        return context