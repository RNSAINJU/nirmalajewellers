from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import IntegerField, Q, Sum
from django.db.models.functions import Cast
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.utils.decorators import method_decorator

import openpyxl
from openpyxl.utils import get_column_letter

from common.nepali_utils import ndt
from .forms import CustomerPurchaseForm, MetalStockForm
from .models import (
    CustomerPurchase,
    GoldSilverPurchase,
    MetalStock,
    MetalStockMovement,
    MetalStockType,
    Party,
)
from ornament.models import Kaligar, MainCategory, Ornament, SubCategory
from order.models import Order, OrderMetalStock, OrderOrnament, OrderPayment
from sales.models import Sale, SalesMetalStock

# Decimal alias used in a few imports
D = Decimal

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


class PurchaseListView(ListView):
    model = GoldSilverPurchase
    template_name = 'goldsilverpurchase/purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('party')
        date_str = self.request.GET.get('date')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        party_id = self.request.GET.get('party')
        metal_type = self.request.GET.get('metal_type')

        if date_str:
            try:
                y, m, d = map(int, str(date_str).split('-'))
                if ndt:
                    queryset = queryset.filter(bill_date=ndt.date(y, m, d))
            except Exception:
                pass
        elif start_date_str and end_date_str:
            try:
                y1, m1, d1 = map(int, str(start_date_str).split('-'))
                y2, m2, d2 = map(int, str(end_date_str).split('-'))
                if ndt:
                    queryset = queryset.filter(
                        bill_date__range=(ndt.date(y1, m1, d1), ndt.date(y2, m2, d2))
                    )
            except Exception:
                pass

        if party_id:
            queryset = queryset.filter(party_id=party_id)

        if metal_type:
            queryset = queryset.filter(metal_type=metal_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context['total_quantity'] = qs.aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        context['total_amount'] = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

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
        context['metal_type'] = self.request.GET.get('metal_type', '')
        return context
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


# ---------------------- Party Management ----------------------
class PartyCreateView(CreateView):
    model = Party
    fields = ['party_name', 'panno']
    template_name = 'goldsilverpurchase/party_form.html'
    success_url = reverse_lazy('gsp:purchaselist')


class PartyUpdateView(UpdateView):
    model = Party
    fields = ['party_name', 'panno']
    template_name = 'goldsilverpurchase/party_form.html'
    success_url = reverse_lazy('gsp:purchaselist')


class PartyDeleteView(DeleteView):
    model = Party
    template_name = 'goldsilverpurchase/party_confirm_delete.html'
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
    from openpyxl import Workbook
    from django.http import HttpResponse
    wb = Workbook()
    default_ws = wb.active
    wb.remove(default_ws)

    def convert_to_excel_value(val):
        """Convert any value to Excel-safe format (convert dates to strings)"""
        if val is None:
            return ""
        # Convert nepali_datetime.date objects to string
        if hasattr(val, 'strftime'):
            return str(val)
        return val

    def add_sheet(title, headers, rows):
        ws = wb.create_sheet(title=title[:31])
        ws.append(headers)
        for row in rows:
            # Convert all values in row to Excel-safe format
            safe_row = tuple(convert_to_excel_value(v) for v in row)
            ws.append(safe_row)

    # --- Finance Models ---
    from finance.models import EmployeeSalary, SundryCreditor, SundryDebtor, Loan, CreditorTransaction, DebtorTransaction, Expense, Employee
    
    # Employee sheet
    employee_rows = [
        (e.id, e.first_name, e.last_name, e.email, e.phone, e.position, e.base_salary, e.hire_date, e.is_active, e.created_at, e.updated_at) for e in Employee.objects.all().order_by("created_at")
    ]
    add_sheet("Employee", ["ID", "First Name", "Last Name", "Email", "Phone", "Position", "Base Salary", "Hire Date", "Is Active", "Created At", "Updated At"], employee_rows)

    salary_rows = [
        (s.id, s.employee.first_name + ' ' + s.employee.last_name if s.employee else "", s.month, s.total_salary, s.amount_paid, s.status, s.created_at, s.updated_at) for s in EmployeeSalary.objects.select_related('employee').all().order_by("created_at")
    ]
    add_sheet("EmployeeSalary", ["ID", "Employee Name", "Month", "Total Salary", "Amount Paid", "Status", "Created At", "Updated At"], salary_rows)

    # Expense sheet
    expense_rows = [
        (ex.id, ex.category, ex.description, ex.amount, ex.expense_date, ex.notes, ex.created_at, ex.updated_at) for ex in Expense.objects.all().order_by("created_at")
    ]
    add_sheet("Expense", ["ID", "Category", "Description", "Amount", "Expense Date", "Notes", "Created At", "Updated At"], expense_rows)

    creditor_rows = [
        (c.id, c.name, c.bs_date, c.opening_balance, c.current_balance, c.is_paid, c.created_at, c.updated_at) for c in SundryCreditor.objects.all().order_by("created_at")
    ]
    add_sheet("SundryCreditor", ["ID", "Name", "BS Date", "Opening Balance", "Current Balance", "Is Paid", "Created At", "Updated At"], creditor_rows)

    debtor_rows = [
        (d.id, d.name, d.bs_date, d.opening_balance, d.current_balance, d.is_paid, d.created_at, d.updated_at) for d in SundryDebtor.objects.all().order_by("created_at")
    ]
    add_sheet("SundryDebtor", ["ID", "Name", "BS Date", "Opening Balance", "Current Balance", "Is Paid", "Created At", "Updated At"], debtor_rows)

    loan_rows = [
        (l.id, l.bank_name, l.amount, l.interest_rate, l.start_date, l.notes, l.created_at, l.updated_at) for l in Loan.objects.all().order_by("created_at")
    ]
    add_sheet("Loan", ["ID", "Bank Name", "Amount", "Interest Rate", "Start Date", "Notes", "Created At", "Updated At"], loan_rows)

    creditor_tx_rows = [
        (tx.id, tx.creditor.name if tx.creditor else "", tx.transaction_type, tx.reference_no, tx.amount, tx.transaction_date, tx.due_date, tx.created_at) for tx in CreditorTransaction.objects.select_related('creditor').all().order_by("created_at")
    ]
    add_sheet("CreditorTransaction", ["ID", "Creditor Name", "Transaction Type", "Reference No", "Amount", "Transaction Date", "Due Date", "Created At"], creditor_tx_rows)

    # DebtorTransaction model may not exist, check if it's defined
    try:
        debtor_tx_rows = [
            (tx.id, tx.debtor.name if tx.debtor else "", tx.transaction_type, tx.reference_no, tx.amount, tx.transaction_date, tx.due_date, tx.created_at) for tx in DebtorTransaction.objects.select_related('debtor').all().order_by("created_at")
        ]
        add_sheet("DebtorTransaction", ["ID", "Debtor Name", "Transaction Type", "Reference No", "Amount", "Transaction Date", "Due Date", "Created At"], debtor_tx_rows)
    except Exception:
        pass  # Skip if DebtorTransaction doesn't exist or has different structure

    # --- GoldSilverPurchase Models ---
    from goldsilverpurchase.models import GoldSilverPurchase, CustomerPurchase, MetalStock, MetalStockMovement, Party, MetalStockType
    
    # Party sheet
    party_rows = [
        (p.id, p.party_name, p.panno, p.created_at, p.updated_at) for p in Party.objects.all().order_by("created_at")
    ]
    add_sheet("Party", ["ID", "Party Name", "PAN No", "Created At", "Updated At"], party_rows)

    # MetalStockType sheet
    metal_type_rows = [
        (mt.id, mt.name, mt.created_at, mt.updated_at) for mt in MetalStockType.objects.all().order_by("created_at")
    ]
    add_sheet("MetalStockType", ["ID", "Name", "Created At", "Updated At"], metal_type_rows)

    gsp_rows = [
        (p.bill_no, p.bill_date, p.party.party_name if p.party else "", p.particular, p.metal_type, p.purity, p.quantity, p.rate, p.rate_unit, p.wages, p.discount, p.amount, p.payment_mode, p.is_paid, p.remarks, p.created_at, p.updated_at) for p in GoldSilverPurchase.objects.select_related("party").order_by("created_at")
    ]
    add_sheet("GoldSilverPurchase", ["Bill No", "Bill Date", "Party", "Particular", "Metal Type", "Purity", "Quantity", "Rate", "Rate Unit", "Wages", "Discount", "Amount", "Payment Mode", "Is Paid", "Remarks", "Created At", "Updated At"], gsp_rows)

    customer_rows = [
        (cp.sn, cp.purchase_date, cp.customer_name, cp.location, cp.phone_no, cp.metal_type, cp.ornament_name, cp.weight, cp.refined_weight, cp.rate, cp.amount, cp.created_at, cp.updated_at) for cp in CustomerPurchase.objects.order_by("created_at")
    ]
    add_sheet("CustomerPurchase", ["SN", "Purchase Date", "Customer Name", "Location", "Phone", "Metal Type", "Ornament", "Weight", "Refined Weight", "Rate", "Amount", "Created At", "Updated At"], customer_rows)

    metal_stock_rows = [
        (ms.id, ms.metal_type, ms.stock_type.name if ms.stock_type else "", ms.purity, ms.quantity, ms.unit_cost, ms.rate_unit, ms.total_cost, ms.location, ms.remarks, ms.last_updated, ms.created_at) for ms in MetalStock.objects.select_related("stock_type").order_by("created_at")
    ]
    add_sheet("MetalStock", ["ID", "Metal Type", "Stock Type", "Purity", "Quantity", "Unit Cost", "Rate Unit", "Total Cost", "Location", "Remarks", "Last Updated", "Created At"], metal_stock_rows)

    metal_movement_rows = [
        (msm.id, msm.metal_stock_id, msm.movement_type, msm.quantity, msm.rate, msm.reference_type, msm.reference_id, msm.notes, msm.movement_date, msm.created_at) for msm in MetalStockMovement.objects.select_related("metal_stock").order_by("created_at")
    ]
    add_sheet("MetalStockMovement", ["ID", "Metal Stock ID", "Movement Type", "Quantity", "Rate", "Reference Type", "Reference ID", "Notes", "Movement Date", "Created At"], metal_movement_rows)

    # --- Main Models ---
    from main.models import Stock, DailyRate
    
    stock_rows = [
        (s.id, s.year, s.diamond, s.gold, s.silver, s.jardi, s.wages, s.gold_silver_rate_unit, s.diamond_rate, s.gold_rate, s.silver_rate, s.created_at, s.updated_at) for s in Stock.objects.order_by("year")
    ]
    add_sheet("Stock", ["ID", "Year", "Diamond", "Gold", "Silver", "Jardi", "Wages", "Rate Unit", "Diamond Rate", "Gold Rate", "Silver Rate", "Created At", "Updated At"], stock_rows)

    daily_rate_rows = [
        (dr.id, dr.bs_date, dr.gold_rate, dr.silver_rate, dr.gold_rate_10g, dr.silver_rate_10g, dr.created_at, dr.updated_at) for dr in DailyRate.objects.order_by("-created_at")
    ]
    add_sheet("DailyRate", ["ID", "BS Date", "Gold Rate", "Silver Rate", "Gold Rate 10g", "Silver Rate 10g", "Created At", "Updated At"], daily_rate_rows)

    # --- Ornament Models ---
    from ornament.models import Stone, Motimala, Potey, MainCategory, SubCategory, Kaligar, Kaligar_Ornaments, Kaligar_CashAccount, Kaligar_GoldAccount, Ornament
    
    # Stone sheet
    stone_rows = [
        (st.id, st.name, st.cost_per_carat, st.carat, st.cost_price, st.sales_per_carat, st.sales_price, st.profit, st.created_at, st.updated_at) for st in Stone.objects.all().order_by("created_at")
    ]
    add_sheet("Stone", ["ID", "Name", "Cost Per Carat", "Carat", "Cost Price", "Sales Per Carat", "Sales Price", "Profit", "Created At", "Updated At"], stone_rows)

    # Motimala sheet
    motimala_rows = [
        (m.id, m.name, m.cost_per_mala, m.quantity, m.cost_price, m.sales_per_mala, m.sales_price, m.profit, m.created_at, m.updated_at) for m in Motimala.objects.all().order_by("created_at")
    ]
    add_sheet("Motimala", ["ID", "Name", "Cost Per Mala", "Quantity", "Cost Price", "Sales Per Mala", "Sales Price", "Profit", "Created At", "Updated At"], motimala_rows)

    # Potey sheet
    potey_rows = [
        (p.id, p.name, p.loon, p.cost_per_loon, p.cost_price, p.sales_per_loon, p.sales_price, p.profit, p.created_at, p.updated_at) for p in Potey.objects.all().order_by("created_at")
    ]
    add_sheet("Potey", ["ID", "Name", "Loon", "Cost Per Loon", "Cost Price", "Sales Per Loon", "Sales Price", "Profit", "Created At", "Updated At"], potey_rows)

    # MainCategory sheet
    main_cat_rows = [
        (mc.id, mc.name, mc.created_at, mc.updated_at) for mc in MainCategory.objects.all().order_by("created_at")
    ]
    add_sheet("MainCategory", ["ID", "Name", "Created At", "Updated At"], main_cat_rows)

    # SubCategory sheet
    sub_cat_rows = [
        (sc.id, sc.name, sc.main_category.name if sc.main_category else "", sc.created_at, sc.updated_at) for sc in SubCategory.objects.select_related("main_category").all().order_by("created_at")
    ]
    add_sheet("SubCategory", ["ID", "Name", "Main Category", "Created At", "Updated At"], sub_cat_rows)

    # Ornament sheet
    ornament_rows = [
        (o.id, o.ornament_name, o.category, o.ornament_type, o.metal_type, o.weight, o.purity, o.rate, o.status, o.stock_date, o.sold_date, o.created_at, o.updated_at) for o in Ornament.objects.all().order_by("created_at")
    ]
    add_sheet("Ornament", ["ID", "Name", "Category", "Type", "Metal Type", "Weight", "Purity", "Rate", "Status", "Stock Date", "Sold Date", "Created At", "Updated At"], ornament_rows)

    # Kaligar sheet
    kaligar_rows = [
        (k.id, k.name, k.address, k.phone, k.created_at, k.updated_at) for k in Kaligar.objects.all().order_by("created_at")
    ]
    add_sheet("Kaligar", ["ID", "Name", "Address", "Phone", "Created At", "Updated At"], kaligar_rows)

    # Kaligar_Ornaments sheet
    kaligar_orn_rows = [
        (ko.id, ko.kaligar.name if ko.kaligar else "", ko.ornament_name, ko.metal_type, ko.quantity, ko.weight_per_piece, ko.total_weight, ko.created_at, ko.updated_at) for ko in Kaligar_Ornaments.objects.select_related("kaligar").all().order_by("created_at")
    ]
    add_sheet("Kaligar_Ornaments", ["ID", "Kaligar", "Ornament Name", "Metal Type", "Quantity", "Weight Per Piece", "Total Weight", "Created At", "Updated At"], kaligar_orn_rows)

    # Kaligar_CashAccount sheet
    kaligar_cash_rows = [
        (kc.id, kc.kaligar.name if kc.kaligar else "", kc.debit, kc.credit, kc.date, kc.description, kc.created_at, kc.updated_at) for kc in Kaligar_CashAccount.objects.select_related("kaligar").all().order_by("created_at")
    ]
    add_sheet("Kaligar_CashAccount", ["ID", "Kaligar", "Debit", "Credit", "Date", "Description", "Created At", "Updated At"], kaligar_cash_rows)

    # Kaligar_GoldAccount sheet
    kaligar_gold_rows = [
        (kg.id, kg.kaligar.name if kg.kaligar else "", kg.gold_in, kg.gold_out, kg.date, kg.description, kg.created_at, kg.updated_at) for kg in Kaligar_GoldAccount.objects.select_related("kaligar").all().order_by("created_at")
    ]
    add_sheet("Kaligar_GoldAccount", ["ID", "Kaligar", "Gold In", "Gold Out", "Date", "Description", "Created At", "Updated At"], kaligar_gold_rows)

    # --- Order Models ---
    from order.models import Order, OrderMetalStock, OrderPayment, OrderOrnament, DebtorPayment
    
    order_rows = [
        (o.sn, o.order_date, o.deliver_date, o.customer_name, o.phone_number, o.status, o.order_type, o.description, o.discount, o.amount, o.subtotal, o.tax, o.total, o.remaining_amount, o.created_at, o.updated_at) for o in Order.objects.order_by("created_at")
    ]
    add_sheet("Order", ["SN", "Order Date", "Deliver Date", "Customer Name", "Phone", "Status", "Order Type", "Description", "Discount", "Amount", "Subtotal", "Tax", "Total", "Remaining Amount", "Created At", "Updated At"], order_rows)

    order_metal_rows = [
        (oms.order_id, oms.stock_type.name if oms.stock_type else "", oms.metal_type, oms.purity, oms.quantity, oms.rate_per_gram, oms.rate_unit, oms.line_amount, oms.remarks, oms.created_at, oms.updated_at) for oms in OrderMetalStock.objects.select_related("order", "stock_type").order_by("created_at")
    ]
    add_sheet("OrderMetalStock", ["Order ID", "Stock Type", "Metal Type", "Purity", "Quantity", "Rate Per Gram", "Rate Unit", "Line Amount", "Remarks", "Created At", "Updated At"], order_metal_rows)

    payment_rows = [
        (op.order_id, op.payment_mode, op.amount, op.created_at, op.updated_at) for op in OrderPayment.objects.select_related("order").order_by("created_at")
    ]
    add_sheet("OrderPayment", ["Order ID", "Payment Mode", "Amount", "Created At", "Updated At"], payment_rows)

    order_ornament_rows = [
        (oo.order_id, oo.ornament_id, oo.gold_rate, oo.diamond_rate, oo.zircon_rate, oo.stone_rate, oo.jarti, oo.jyala, oo.line_amount, oo.created_at, oo.updated_at) for oo in OrderOrnament.objects.select_related("order", "ornament").order_by("created_at")
    ]
    add_sheet("OrderOrnament", ["Order ID", "Ornament ID", "Gold Rate", "Diamond Rate", "Zircon Rate", "Stone Rate", "Jarti", "Jyala", "Line Amount", "Created At", "Updated At"], order_ornament_rows)

    # DebtorPayment sheet
    debtor_payment_rows = [
        (dp.id, dp.order_payment.order_id, dp.debtor.name if dp.debtor else "", dp.transaction_type, dp.created_at, dp.updated_at) for dp in DebtorPayment.objects.select_related("order_payment__order", "debtor").all().order_by("created_at")
    ]
    add_sheet("DebtorPayment", ["ID", "Order ID", "Debtor Name", "Transaction Type", "Created At", "Updated At"], debtor_payment_rows)

    # --- Sales Models ---
    from sales.models import Sale, SalesMetalStock
    sale_rows = [
        (s.order_id, s.bill_no, s.sale_date, s.created_at, s.updated_at) for s in Sale.objects.select_related("order").order_by("created_at")
    ]
    add_sheet("Sale", ["Order ID", "Bill No", "Sale Date", "Created At", "Updated At"], sale_rows)

    sales_metal_rows = [
        (sms.sale_id, sms.stock_type.name if sms.stock_type else "", sms.metal_type, sms.purity, sms.quantity, sms.rate_per_gram, sms.rate_unit, sms.line_amount, sms.remarks, sms.created_at, sms.updated_at) for sms in SalesMetalStock.objects.select_related("sale", "stock_type").order_by("created_at")
    ]
    add_sheet("SalesMetalStock", ["Sale ID", "Stock Type", "Metal Type", "Purity", "Quantity", "Rate Per Gram", "Rate Unit", "Line Amount", "Remarks", "Created At", "Updated At"], sales_metal_rows)
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
        ornament_id_map = {}

        def to_date(val):
            if not val:
                return None
            try:
                if isinstance(val, str):
                    y, m, d = map(int, val.split("-"))
                    return ndt.date(y, m, d) if ndt else None
                return val
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
                                panno="000000000",
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

                    orn_id = int(orn_id) if orn_id else None

                    if code:
                        existing = Ornament.objects.filter(code=str(code)).first()
                        if existing:
                            ornament_id_map[orn_id] = existing.id
                            continue

                    main_cat = None
                    if main_category:
                        main_cat, _ = MainCategory.objects.get_or_create(name=main_category)

                    sub_cat = None
                    if sub_category:
                        sub_cat, _ = SubCategory.objects.get_or_create(name=sub_category)

                    kaligar = None
                    if kaligar_name:
                        kaligar, _ = Kaligar.objects.get_or_create(
                            name=kaligar_name,
                            defaults={"panno": "000000000"},
                        )
                    else:
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
                        ornament_id = int(ornament_id) if ornament_id else None
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
                            errors.append(
                                f"OrderOrnaments row {row_num}: Ornament ID {ornament_id} not found in mapping"
                            )
                    except Order.DoesNotExist:
                        errors.append(f"OrderOrnaments row {row_num}: Order SN {order_sn} not found")
                    except Ornament.DoesNotExist:
                        errors.append(
                            f"OrderOrnaments row {row_num}: Ornament ID {mapped_ornament_id} not found after mapping"
                        )
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


def export_all_data_json(request):
    """Export all data as JSON for faster backups - includes all models from all apps."""
    import json
    from decimal import Decimal
    from datetime import datetime

    def json_serializer(obj):
        """Custom JSON serializer for Decimal and date objects."""
        if isinstance(obj, Decimal):
            return str(obj)
        if hasattr(obj, 'strftime'):  # Handles both datetime and nepali_datetime.date
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    try:
        data = {}

        # --- Finance Models ---
        from finance.models import EmployeeSalary, SundryCreditor, SundryDebtor, Loan, CreditorTransaction, DebtorTransaction, Expense, Employee
        
        data['Employee'] = [
            {
                'id': e.id,
                'first_name': e.first_name,
                'last_name': e.last_name,
                'email': e.email,
                'phone': e.phone,
                'position': e.position,
                'base_salary': str(e.base_salary),
                'hire_date': str(e.hire_date) if e.hire_date else None,
                'is_active': e.is_active,
                'created_at': str(e.created_at),
                'updated_at': str(e.updated_at),
            }
            for e in Employee.objects.all()
        ]

        data['EmployeeSalary'] = [
            {
                'id': s.id,
                'employee_name': s.employee.first_name + ' ' + s.employee.last_name if s.employee else "",
                'month': str(s.month),
                'total_salary': str(s.total_salary),
                'amount_paid': str(s.amount_paid),
                'status': s.status,
                'created_at': str(s.created_at),
                'updated_at': str(s.updated_at),
            }
            for s in EmployeeSalary.objects.select_related('employee').all()
        ]

        data['Expense'] = [
            {
                'id': ex.id,
                'category': ex.category,
                'description': ex.description,
                'amount': str(ex.amount),
                'expense_date': str(ex.expense_date),
                'notes': ex.notes,
                'created_at': str(ex.created_at),
                'updated_at': str(ex.updated_at),
            }
            for ex in Expense.objects.all()
        ]

        data['SundryCreditor'] = [
            {
                'id': c.id,
                'name': c.name,
                'bs_date': str(c.bs_date) if c.bs_date else None,
                'opening_balance': str(c.opening_balance),
                'current_balance': str(c.current_balance),
                'is_paid': c.is_paid,
                'created_at': str(c.created_at),
                'updated_at': str(c.updated_at),
            }
            for c in SundryCreditor.objects.all()
        ]

        data['SundryDebtor'] = [
            {
                'id': d.id,
                'name': d.name,
                'bs_date': str(d.bs_date) if d.bs_date else None,
                'opening_balance': str(d.opening_balance),
                'current_balance': str(d.current_balance),
                'is_paid': d.is_paid,
                'created_at': str(d.created_at),
                'updated_at': str(d.updated_at),
            }
            for d in SundryDebtor.objects.all()
        ]

        data['Loan'] = [
            {
                'id': l.id,
                'bank_name': l.bank_name,
                'amount': str(l.amount),
                'interest_rate': str(l.interest_rate),
                'start_date': str(l.start_date),
                'notes': l.notes,
                'created_at': str(l.created_at),
                'updated_at': str(l.updated_at),
            }
            for l in Loan.objects.all()
        ]

        data['CreditorTransaction'] = [
            {
                'id': tx.id,
                'creditor_name': tx.creditor.name if tx.creditor else "",
                'transaction_type': tx.transaction_type,
                'reference_no': tx.reference_no,
                'amount': str(tx.amount),
                'transaction_date': str(tx.transaction_date),
                'due_date': str(tx.due_date) if tx.due_date else None,
                'created_at': str(tx.created_at),
            }
            for tx in CreditorTransaction.objects.select_related('creditor').all()
        ]

        data['DebtorTransaction'] = [
            {
                'id': tx.id,
                'debtor_name': tx.debtor.name if tx.debtor else "",
                'transaction_type': tx.transaction_type,
                'reference_no': tx.reference_no,
                'amount': str(tx.amount),
                'transaction_date': str(tx.transaction_date),
                'due_date': str(tx.due_date) if tx.due_date else None,
                'created_at': str(tx.created_at),
            }
            for tx in DebtorTransaction.objects.select_related('debtor').all()
        ]

        # --- GoldSilverPurchase Models ---
        from goldsilverpurchase.models import GoldSilverPurchase, CustomerPurchase, MetalStock, MetalStockMovement, Party, MetalStockType
        
        data['Party'] = [
            {
                'id': p.id,
                'party_name': p.party_name,
                'panno': p.panno,
                'created_at': str(p.created_at),
                'updated_at': str(p.updated_at),
            }
            for p in Party.objects.all()
        ]

        data['MetalStockType'] = [
            {
                'id': mt.id,
                'name': mt.name,
                'created_at': str(mt.created_at),
                'updated_at': str(mt.updated_at),
            }
            for mt in MetalStockType.objects.all()
        ]

        data['GoldSilverPurchase'] = [
            {
                'bill_no': p.bill_no,
                'bill_date': str(p.bill_date),
                'party_name': p.party.party_name if p.party else "",
                'particular': p.particular,
                'metal_type': p.metal_type,
                'purity': p.purity,
                'quantity': str(p.quantity),
                'rate': str(p.rate),
                'rate_unit': p.rate_unit,
                'wages': str(p.wages),
                'discount': str(p.discount),
                'amount': str(p.amount),
                'payment_mode': p.payment_mode,
                'is_paid': p.is_paid,
                'remarks': p.remarks,
                'created_at': str(p.created_at),
                'updated_at': str(p.updated_at),
            }
            for p in GoldSilverPurchase.objects.select_related("party").all()
        ]

        data['CustomerPurchase'] = [
            {
                'sn': cp.sn,
                'purchase_date': str(cp.purchase_date) if cp.purchase_date else None,
                'customer_name': cp.customer_name,
                'location': cp.location,
                'phone_no': cp.phone_no,
                'metal_type': cp.metal_type,
                'ornament_name': cp.ornament_name,
                'weight': str(cp.weight),
                'refined_weight': str(cp.refined_weight),
                'rate': str(cp.rate),
                'amount': str(cp.amount),
                'created_at': str(cp.created_at),
                'updated_at': str(cp.updated_at),
            }
            for cp in CustomerPurchase.objects.all()
        ]

        data['MetalStock'] = [
            {
                'id': ms.id,
                'metal_type': ms.metal_type,
                'stock_type': ms.stock_type.name if ms.stock_type else "",
                'purity': ms.purity,
                'quantity': str(ms.quantity),
                'unit_cost': str(ms.unit_cost),
                'rate_unit': ms.rate_unit,
                'total_cost': str(ms.total_cost),
                'location': ms.location,
                'remarks': ms.remarks,
                'created_at': str(ms.created_at),
                'updated_at': str(ms.updated_at),
            }
            for ms in MetalStock.objects.select_related("stock_type").all()
        ]

        data['MetalStockMovement'] = [
            {
                'id': msm.id,
                'metal_stock_id': msm.metal_stock_id,
                'movement_type': msm.movement_type,
                'quantity': str(msm.quantity),
                'rate': str(msm.rate),
                'reference_type': msm.reference_type,
                'reference_id': msm.reference_id,
                'notes': msm.notes,
                'movement_date': str(msm.movement_date) if msm.movement_date else None,
                'created_at': str(msm.created_at),
                'updated_at': str(msm.updated_at),
            }
            for msm in MetalStockMovement.objects.all()
        ]

        # --- Main Models ---
        from main.models import Stock, DailyRate
        
        data['Stock'] = [
            {
                'id': s.id,
                'year': s.year,
                'diamond': str(s.diamond),
                'gold': str(s.gold),
                'silver': str(s.silver),
                'jardi': str(s.jardi),
                'wages': str(s.wages),
                'gold_silver_rate_unit': s.gold_silver_rate_unit,
                'diamond_rate': str(s.diamond_rate),
                'gold_rate': str(s.gold_rate),
                'silver_rate': str(s.silver_rate),
                'created_at': str(s.created_at),
                'updated_at': str(s.updated_at),
            }
            for s in Stock.objects.all()
        ]

        data['DailyRate'] = [
            {
                'id': dr.id,
                'bs_date': dr.bs_date,
                'gold_rate': str(dr.gold_rate),
                'silver_rate': str(dr.silver_rate),
                'gold_rate_10g': str(dr.gold_rate_10g),
                'silver_rate_10g': str(dr.silver_rate_10g),
                'created_at': str(dr.created_at),
                'updated_at': str(dr.updated_at),
            }
            for dr in DailyRate.objects.all()
        ]

        # --- Ornament Models ---
        from ornament.models import Stone, Motimala, Potey, MainCategory, SubCategory, Kaligar, Kaligar_Ornaments, Kaligar_CashAccount, Kaligar_GoldAccount, Ornament
        
        data['Stone'] = [
            {
                'id': st.id,
                'name': st.name,
                'cost_per_carat': str(st.cost_per_carat),
                'carat': str(st.carat),
                'cost_price': str(st.cost_price),
                'sales_per_carat': str(st.sales_per_carat),
                'sales_price': str(st.sales_price),
                'profit': str(st.profit),
                'created_at': str(st.created_at),
                'updated_at': str(st.updated_at),
            }
            for st in Stone.objects.all()
        ]

        data['Motimala'] = [
            {
                'id': m.id,
                'name': m.name,
                'cost_per_mala': str(m.cost_per_mala),
                'quantity': m.quantity,
                'cost_price': str(m.cost_price),
                'sales_per_mala': str(m.sales_per_mala),
                'sales_price': str(m.sales_price),
                'profit': str(m.profit),
                'created_at': str(m.created_at),
                'updated_at': str(m.updated_at),
            }
            for m in Motimala.objects.all()
        ]

        data['Potey'] = [
            {
                'id': p.id,
                'name': p.name,
                'loon': p.loon,
                'cost_per_loon': str(p.cost_per_loon),
                'cost_price': str(p.cost_price),
                'sales_per_loon': str(p.sales_per_loon),
                'sales_price': str(p.sales_price),
                'profit': str(p.profit),
                'created_at': str(p.created_at),
                'updated_at': str(p.updated_at),
            }
            for p in Potey.objects.all()
        ]

        data['MainCategory'] = [
            {
                'id': mc.id,
                'name': mc.name,
                'created_at': str(mc.created_at),
                'updated_at': str(mc.updated_at),
            }
            for mc in MainCategory.objects.all()
        ]

        data['SubCategory'] = [
            {
                'id': sc.id,
                'name': sc.name,
                'main_category': sc.main_category.name if sc.main_category else "",
                'created_at': str(sc.created_at),
                'updated_at': str(sc.updated_at),
            }
            for sc in SubCategory.objects.select_related("main_category").all()
        ]

        data['Ornament'] = [
            {
                'id': o.id,
                'ornament_name': o.ornament_name,
                'category': o.category,
                'ornament_type': o.ornament_type,
                'metal_type': o.metal_type,
                'weight': str(o.weight),
                'purity': o.purity,
                'rate': str(o.rate),
                'status': o.status,
                'stock_date': str(o.stock_date) if o.stock_date else None,
                'sold_date': str(o.sold_date) if o.sold_date else None,
                'created_at': str(o.created_at),
                'updated_at': str(o.updated_at),
            }
            for o in Ornament.objects.all()
        ]

        data['Kaligar'] = [
            {
                'id': k.id,
                'name': k.name,
                'address': k.address,
                'phone': k.phone,
                'created_at': str(k.created_at),
                'updated_at': str(k.updated_at),
            }
            for k in Kaligar.objects.all()
        ]

        data['Kaligar_Ornaments'] = [
            {
                'id': ko.id,
                'kaligar': ko.kaligar.name if ko.kaligar else "",
                'ornament_name': ko.ornament_name,
                'metal_type': ko.metal_type,
                'quantity': ko.quantity,
                'weight_per_piece': str(ko.weight_per_piece) if ko.weight_per_piece else None,
                'total_weight': str(ko.total_weight) if ko.total_weight else None,
                'created_at': str(ko.created_at),
                'updated_at': str(ko.updated_at),
            }
            for ko in Kaligar_Ornaments.objects.select_related("kaligar").all()
        ]

        data['Kaligar_CashAccount'] = [
            {
                'id': kc.id,
                'kaligar': kc.kaligar.name if kc.kaligar else "",
                'debit': str(kc.debit) if kc.debit else None,
                'credit': str(kc.credit) if kc.credit else None,
                'date': str(kc.date) if kc.date else None,
                'description': kc.description,
                'created_at': str(kc.created_at),
                'updated_at': str(kc.updated_at),
            }
            for kc in Kaligar_CashAccount.objects.select_related("kaligar").all()
        ]

        data['Kaligar_GoldAccount'] = [
            {
                'id': kg.id,
                'kaligar': kg.kaligar.name if kg.kaligar else "",
                'gold_in': str(kg.gold_in) if kg.gold_in else None,
                'gold_out': str(kg.gold_out) if kg.gold_out else None,
                'date': str(kg.date) if kg.date else None,
                'description': kg.description,
                'created_at': str(kg.created_at),
                'updated_at': str(kg.updated_at),
            }
            for kg in Kaligar_GoldAccount.objects.select_related("kaligar").all()
        ]

        # --- Order Models ---
        from order.models import Order, OrderMetalStock, OrderPayment, OrderOrnament, DebtorPayment
        
        data['Order'] = [
            {
                'sn': o.sn,
                'order_date': str(o.order_date) if o.order_date else None,
                'deliver_date': str(o.deliver_date) if o.deliver_date else None,
                'customer_name': o.customer_name,
                'phone_number': o.phone_number,
                'status': o.status,
                'order_type': o.order_type,
                'description': o.description,
                'discount': str(o.discount),
                'amount': str(o.amount),
                'subtotal': str(o.subtotal),
                'tax': str(o.tax),
                'total': str(o.total),
                'remaining_amount': str(o.remaining_amount),
                'created_at': str(o.created_at),
                'updated_at': str(o.updated_at),
            }
            for o in Order.objects.all()
        ]

        data['OrderMetalStock'] = [
            {
                'id': oms.id,
                'order_id': oms.order_id,
                'stock_type': oms.stock_type.name if oms.stock_type else "",
                'metal_type': oms.metal_type,
                'purity': oms.purity,
                'quantity': str(oms.quantity),
                'rate_per_gram': str(oms.rate_per_gram),
                'rate_unit': oms.rate_unit,
                'line_amount': str(oms.line_amount),
                'remarks': oms.remarks,
                'created_at': str(oms.created_at),
                'updated_at': str(oms.updated_at),
            }
            for oms in OrderMetalStock.objects.select_related("stock_type").all()
        ]

        data['OrderPayment'] = [
            {
                'id': op.id,
                'order_id': op.order_id,
                'payment_mode': op.payment_mode,
                'amount': str(op.amount),
                'created_at': str(op.created_at),
                'updated_at': str(op.updated_at),
            }
            for op in OrderPayment.objects.all()
        ]

        data['OrderOrnament'] = [
            {
                'id': oo.id,
                'order_id': oo.order_id,
                'ornament_id': oo.ornament_id,
                'gold_rate': str(oo.gold_rate),
                'diamond_rate': str(oo.diamond_rate),
                'zircon_rate': str(oo.zircon_rate),
                'stone_rate': str(oo.stone_rate),
                'jarti': str(oo.jarti),
                'jyala': str(oo.jyala),
                'line_amount': str(oo.line_amount),
                'created_at': str(oo.created_at),
                'updated_at': str(oo.updated_at),
            }
            for oo in OrderOrnament.objects.all()
        ]

        data['DebtorPayment'] = [
            {
                'id': dp.id,
                'order_id': dp.order_payment.order_id,
                'debtor_name': dp.debtor.name if dp.debtor else "",
                'transaction_type': dp.transaction_type,
                'created_at': str(dp.created_at),
                'updated_at': str(dp.updated_at),
            }
            for dp in DebtorPayment.objects.select_related("order_payment__order", "debtor").all()
        ]

        # --- Sales Models ---
        from sales.models import Sale, SalesMetalStock
        
        data['Sale'] = [
            {
                'id': s.id,
                'order_id': s.order_id,
                'bill_no': s.bill_no,
                'sale_date': str(s.sale_date) if s.sale_date else None,
                'created_at': str(s.created_at),
                'updated_at': str(s.updated_at),
            }
            for s in Sale.objects.all()
        ]

        data['SalesMetalStock'] = [
            {
                'id': sms.id,
                'sale_id': sms.sale_id,
                'stock_type': sms.stock_type.name if sms.stock_type else "",
                'metal_type': sms.metal_type,
                'purity': sms.purity,
                'quantity': str(sms.quantity),
                'rate_per_gram': str(sms.rate_per_gram),
                'rate_unit': sms.rate_unit,
                'line_amount': str(sms.line_amount),
                'remarks': sms.remarks,
                'created_at': str(sms.created_at),
                'updated_at': str(sms.updated_at),
            }
            for sms in SalesMetalStock.objects.select_related("stock_type").all()
        ]

        # Create JSON response
        json_str = json.dumps(data, default=json_serializer, indent=2)
        response = HttpResponse(json_str, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename=all_data_backup.json'
        return response

    except Exception as e:
        messages.error(None, f"Error exporting JSON: {str(e)}")
        return HttpResponse(f"Export failed: {str(e)}", status=500)


def import_all_data_json(request):
    """Import all data from a JSON file for faster restoration."""
    import json
    
    if request.method != "POST" or "import_file" not in request.FILES:
        return redirect("gsp:data_settings")

    file = request.FILES.get("import_file")
    if not file:
        messages.error(request, "Please upload a JSON file.")
        return redirect("gsp:data_settings")

    try:
        # Read and parse JSON
        file_content = file.read().decode('utf-8')
        data = json.loads(file_content)
        imported_count = {}

        # --- Import GoldSilverPurchase ---
        if "GoldSilverPurchase" in data:
            count = 0
            for row in data["GoldSilverPurchase"]:
                try:
                    if GoldSilverPurchase.objects.filter(bill_no=str(row['bill_no'])).exists():
                        continue

                    party = None
                    if row.get('party_name'):
                        party = Party.objects.filter(party_name=row['party_name']).first()
                        if not party:
                            party = Party.objects.create(
                                party_name=row['party_name'],
                                panno="000000000",
                            )

                    GoldSilverPurchase.objects.create(
                        bill_no=str(row['bill_no']),
                        bill_date=ndt.date(*map(int, str(row['bill_date']).split('-'))) if ndt and row.get('bill_date') else None,
                        party=party,
                        particular=row.get('particular'),
                        metal_type=row.get('metal_type', 'gold'),
                        purity=row.get('purity', '22K'),
                        quantity=to_decimal(row.get('quantity', 0)),
                        rate=to_decimal(row.get('rate', 0)),
                        rate_unit=row.get('rate_unit', 'tola'),
                        wages=to_decimal(row.get('wages', 0)),
                        discount=to_decimal(row.get('discount', 0)),
                        amount=to_decimal(row.get('amount', 0)),
                        payment_mode=row.get('payment_mode', 'cash'),
                        is_paid=row.get('is_paid', False),
                        remarks=row.get('remarks', ''),
                    )
                    count += 1
                except Exception as e:
                    messages.warning(request, f"Skipped GoldSilverPurchase {row.get('bill_no')}: {e}")
            imported_count['GoldSilverPurchase'] = count

        # --- Import CustomerPurchase ---
        if "CustomerPurchase" in data:
            count = 0
            for row in data["CustomerPurchase"]:
                try:
                    if CustomerPurchase.objects.filter(sn=str(row['sn'])).exists():
                        continue

                    CustomerPurchase.objects.create(
                        sn=str(row['sn']),
                        purchase_date=ndt.date(*map(int, str(row['purchase_date']).split('-'))) if ndt and row.get('purchase_date') else None,
                        customer_name=row.get('customer_name', ''),
                        location=row.get('location', ''),
                        phone_no=row.get('phone_no', ''),
                        metal_type=row.get('metal_type', 'gold'),
                        ornament_name=row.get('ornament_name', ''),
                        weight=to_decimal(row.get('weight', 0)),
                        refined_weight=to_decimal(row.get('refined_weight', 0)),
                        rate=to_decimal(row.get('rate', 0)),
                        amount=to_decimal(row.get('amount', 0)),
                    )
                    count += 1
                except Exception as e:
                    messages.warning(request, f"Skipped CustomerPurchase {row.get('sn')}: {e}")
            imported_count['CustomerPurchase'] = count

        # --- Import Orders ---
        if "Order" in data:
            count = 0
            for row in data["Order"]:
                try:
                    if Order.objects.filter(sn=row['sn']).exists():
                        continue

                    Order.objects.create(
                        sn=row['sn'],
                        order_date=ndt.date(*map(int, str(row['order_date']).split('-'))) if ndt and row.get('order_date') else None,
                        deliver_date=ndt.date(*map(int, str(row['deliver_date']).split('-'))) if ndt and row.get('deliver_date') else None,
                        customer_name=row.get('customer_name', ''),
                        phone_number=row.get('phone_number', ''),
                        status=row.get('status', 'order'),
                        order_type=row.get('order_type', 'custom'),
                        description=row.get('description', ''),
                        discount=to_decimal(row.get('discount', 0)),
                        amount=to_decimal(row.get('amount', 0)),
                        subtotal=to_decimal(row.get('subtotal', 0)),
                        tax=to_decimal(row.get('tax', 0)),
                        total=to_decimal(row.get('total', 0)),
                        remaining_amount=to_decimal(row.get('remaining_amount', 0)),
                    )
                    count += 1
                except Exception as e:
                    messages.warning(request, f"Skipped Order {row.get('sn')}: {e}")
            imported_count['Order'] = count

        # --- Import OrderPayments ---
        if "OrderPayment" in data:
            count = 0
            for row in data["OrderPayment"]:
                try:
                    try:
                        order = Order.objects.get(sn=row['order_id'])
                        OrderPayment.objects.create(
                            order=order,
                            payment_mode=row.get('payment_mode', 'cash'),
                            amount=to_decimal(row.get('amount', 0)),
                        )
                        count += 1
                    except Order.DoesNotExist:
                        pass
                except Exception as e:
                    messages.warning(request, f"Skipped OrderPayment: {e}")
            imported_count['OrderPayment'] = count

        # --- Import Sales ---
        if "Sale" in data:
            count = 0
            for row in data["Sale"]:
                try:
                    try:
                        order = Order.objects.get(sn=row['order_id'])
                        if not Sale.objects.filter(order=order).exists():
                            Sale.objects.create(
                                order=order,
                                bill_no=row.get('bill_no'),
                                sale_date=ndt.date(*map(int, str(row['sale_date']).split('-'))) if ndt and row.get('sale_date') else None,
                            )
                            count += 1
                    except Order.DoesNotExist:
                        pass
                except Exception as e:
                    messages.warning(request, f"Skipped Sale: {e}")
            imported_count['Sale'] = count

        summary = " | ".join([f"{k}: {v}" for k, v in imported_count.items() if v > 0])
        messages.success(request, f"JSON import completed: {summary}")
        return redirect("gsp:data_settings")

    except json.JSONDecodeError:
        messages.error(request, "Invalid JSON file format.")
        return redirect("gsp:data_settings")
    except Exception as e:
        messages.error(request, f"Import failed: {str(e)}")
        return redirect("gsp:data_settings")


def delete_all_data(request):
    """Delete all data from ALL tables across all apps (with confirmation)."""
    if request.method != "POST":
        return redirect("gsp:data_settings")

    # Verify confirmation token to prevent accidental deletion
    confirm_token = request.POST.get("confirm_delete")
    if confirm_token != "DELETE_ALL_DATA_CONFIRMED":
        messages.error(request, "Deletion not confirmed. Data was not deleted.")
        return redirect("gsp:data_settings")

    try:
        # Import all models
        from finance.models import (
            EmployeeSalary, Expense, Employee,
            CreditorTransaction, DebtorTransaction,
            SundryCreditor, SundryDebtor, Loan
        )
        from goldsilverpurchase.models import (
            MetalStockMovement, MetalStock, CustomerPurchase, 
            GoldSilverPurchase, Party, MetalStockType
        )
        from main.models import DailyRate, Stock
        from ornament.models import (
            Kaligar_CashAccount, Kaligar_GoldAccount, Kaligar_Ornaments,
            Ornament, Kaligar, SubCategory, MainCategory,
            Potey, Motimala, Stone
        )
        from order.models import (
            DebtorPayment, OrderPayment, OrderOrnament, OrderMetalStock, Order
        )
        from sales.models import SalesMetalStock, Sale
        
        deleted_counts = {}
        
        # Delete in reverse dependency order (children first, parents last)
        
        # Sales (dependent on Order)
        deleted_counts['SalesMetalStock'] = SalesMetalStock.objects.count()
        SalesMetalStock.objects.all().delete()
        
        deleted_counts['Sale'] = Sale.objects.count()
        Sale.objects.all().delete()
        
        # Order dependencies
        deleted_counts['DebtorPayment'] = DebtorPayment.objects.count()
        DebtorPayment.objects.all().delete()
        
        deleted_counts['OrderPayment'] = OrderPayment.objects.count()
        OrderPayment.objects.all().delete()
        
        deleted_counts['OrderOrnament'] = OrderOrnament.objects.count()
        OrderOrnament.objects.all().delete()
        
        deleted_counts['OrderMetalStock'] = OrderMetalStock.objects.count()
        OrderMetalStock.objects.all().delete()
        
        deleted_counts['Order'] = Order.objects.count()
        Order.objects.all().delete()
        
        # Ornament models
        deleted_counts['Kaligar_CashAccount'] = Kaligar_CashAccount.objects.count()
        Kaligar_CashAccount.objects.all().delete()
        
        deleted_counts['Kaligar_GoldAccount'] = Kaligar_GoldAccount.objects.count()
        Kaligar_GoldAccount.objects.all().delete()
        
        deleted_counts['Kaligar_Ornaments'] = Kaligar_Ornaments.objects.count()
        Kaligar_Ornaments.objects.all().delete()
        
        deleted_counts['Ornament'] = Ornament.objects.count()
        Ornament.objects.all().delete()
        
        deleted_counts['SubCategory'] = SubCategory.objects.count()
        SubCategory.objects.all().delete()
        
        deleted_counts['MainCategory'] = MainCategory.objects.count()
        MainCategory.objects.all().delete()
        
        deleted_counts['Kaligar'] = Kaligar.objects.count()
        Kaligar.objects.all().delete()
        
        deleted_counts['Potey'] = Potey.objects.count()
        Potey.objects.all().delete()
        
        deleted_counts['Motimala'] = Motimala.objects.count()
        Motimala.objects.all().delete()
        
        deleted_counts['Stone'] = Stone.objects.count()
        Stone.objects.all().delete()
        
        # Main models
        deleted_counts['DailyRate'] = DailyRate.objects.count()
        DailyRate.objects.all().delete()
        
        deleted_counts['Stock'] = Stock.objects.count()
        Stock.objects.all().delete()
        
        # GoldSilverPurchase models
        deleted_counts['MetalStockMovement'] = MetalStockMovement.objects.count()
        MetalStockMovement.objects.all().delete()
        
        deleted_counts['MetalStock'] = MetalStock.objects.count()
        MetalStock.objects.all().delete()
        
        deleted_counts['CustomerPurchase'] = CustomerPurchase.objects.count()
        CustomerPurchase.objects.all().delete()
        
        deleted_counts['GoldSilverPurchase'] = GoldSilverPurchase.objects.count()
        GoldSilverPurchase.objects.all().delete()
        
        deleted_counts['MetalStockType'] = MetalStockType.objects.count()
        MetalStockType.objects.all().delete()
        
        deleted_counts['Party'] = Party.objects.count()
        Party.objects.all().delete()
        
        # Finance models (transactions before parent records)
        deleted_counts['CreditorTransaction'] = CreditorTransaction.objects.count()
        CreditorTransaction.objects.all().delete()
        
        deleted_counts['DebtorTransaction'] = DebtorTransaction.objects.count()
        DebtorTransaction.objects.all().delete()
        
        deleted_counts['EmployeeSalary'] = EmployeeSalary.objects.count()
        EmployeeSalary.objects.all().delete()
        
        deleted_counts['SundryCreditor'] = SundryCreditor.objects.count()
        SundryCreditor.objects.all().delete()
        
        deleted_counts['SundryDebtor'] = SundryDebtor.objects.count()
        SundryDebtor.objects.all().delete()
        
        deleted_counts['Loan'] = Loan.objects.count()
        Loan.objects.all().delete()
        
        deleted_counts['Expense'] = Expense.objects.count()
        Expense.objects.all().delete()
        
        deleted_counts['Employee'] = Employee.objects.count()
        Employee.objects.all().delete()
        
        # Calculate total
        total_deleted = sum(deleted_counts.values())
        
        # Build detailed message
        details = " | ".join([f"{model}: {count}" for model, count in deleted_counts.items() if count > 0])
        
        messages.success(
            request,
            f"All data deleted successfully! Total records removed: {total_deleted}. Details: {details}"
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
    form_class = MetalStockForm
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
    form_class = MetalStockForm
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


def import_wizard(request):
    """Display the import wizard interface."""
    return render(request, 'goldsilverpurchase/import_wizard.html')


def import_wizard_process(request):
    """Process the import with progress tracking."""
    import json
    import openpyxl
    from django.http import JsonResponse
    
    if request.method != "POST" or "import_file" not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'})

    file = request.FILES.get("import_file")
    skip_existing = request.POST.get('skip_existing') == 'on'
    
    if not file:
        return JsonResponse({'success': False, 'error': 'No file provided'})

    imported_count = {}
    skipped_count = {}
    errors = []

    try:
        # Determine file type
        file_ext = file.name.split('.')[-1].lower()
        
        if file_ext == 'json':
            # JSON Import
            file_content = file.read().decode('utf-8')
            data = json.loads(file_content)
            
            # Import in dependency order
            import_order = [
                # Finance (no dependencies)
                'Employee', 'Expense',
                # Finance (with Employee FK)
                'EmployeeSalary',
                # Finance (independent)
                'SundryCreditor', 'SundryDebtor', 'Loan',
                # Finance transactions
                'CreditorTransaction', 'DebtorTransaction',
                # GoldSilverPurchase
                'Party', 'MetalStockType',
                'GoldSilverPurchase', 'CustomerPurchase',
                'MetalStock', 'MetalStockMovement',
                # Main
                'Stock', 'DailyRate',
                # Ornament
                'MainCategory', 'SubCategory', 'Stone', 'Motimala', 'Potey',
                'Kaligar', 'Ornament',
                'Kaligar_Ornaments', 'Kaligar_CashAccount', 'Kaligar_GoldAccount',
                # Orders
                'Order', 'OrderMetalStock', 'OrderPayment', 'OrderOrnament',
                'DebtorPayment',
                # Sales
                'Sale', 'SalesMetalStock',
            ]
            
            for model_name in import_order:
                if model_name not in data:
                    continue
                    
                count, skipped, model_errors = import_model_json(model_name, data[model_name], skip_existing)
                if count > 0:
                    imported_count[model_name] = count
                if skipped > 0:
                    skipped_count[model_name] = skipped
                errors.extend(model_errors)
        
        elif file_ext == 'xlsx':
            # XLSX Import
            wb = openpyxl.load_workbook(file)
            
            # Import in dependency order (same as JSON)
            import_order = [
                'Employee', 'Expense', 'EmployeeSalary',
                'SundryCreditor', 'SundryDebtor', 'Loan',
                'CreditorTransaction', 'DebtorTransaction',
                'Party', 'MetalStockType',
                'GoldSilverPurchase', 'CustomerPurchase',
                'MetalStock', 'MetalStockMovement',
                'Stock', 'DailyRate',
                'MainCategory', 'SubCategory', 'Stone', 'Motimala', 'Potey',
                'Kaligar', 'Ornament',
                'Kaligar_Ornaments', 'Kaligar_CashAccount', 'Kaligar_GoldAccount',
                'Order', 'OrderMetalStock', 'OrderPayment', 'OrderOrnament',
                'DebtorPayment',
                'Sale', 'SalesMetalStock',
            ]
            
            for sheet_name in import_order:
                if sheet_name not in wb.sheetnames:
                    continue
                    
                count, skipped, model_errors = import_model_xlsx(sheet_name, wb[sheet_name], skip_existing)
                if count > 0:
                    imported_count[sheet_name] = count
                if skipped > 0:
                    skipped_count[sheet_name] = skipped
                errors.extend(model_errors)
        
        else:
            return JsonResponse({'success': False, 'error': 'Unsupported file format'})

        return JsonResponse({
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def import_model_json(model_name, records, skip_existing=True):
    """Import a single model from JSON data."""
    from finance.models import Employee, Expense, EmployeeSalary, SundryCreditor, SundryDebtor, Loan, CreditorTransaction, DebtorTransaction
    from goldsilverpurchase.models import Party, MetalStockType, GoldSilverPurchase, CustomerPurchase, MetalStock, MetalStockMovement
    from main.models import Stock, DailyRate
    from ornament.models import Stone, Motimala, Potey, MainCategory, SubCategory, Kaligar, Ornament, Kaligar_Ornaments, Kaligar_CashAccount, Kaligar_GoldAccount
    from order.models import Order, OrderMetalStock, OrderPayment, OrderOrnament, DebtorPayment
    from sales.models import Sale, SalesMetalStock
    
    count = 0
    skipped = 0
    errors = []
    
    # Model mapping
    model_map = {
        'Employee': Employee,
        'Expense': Expense,
        'EmployeeSalary': EmployeeSalary,
        'SundryCreditor': SundryCreditor,
        'SundryDebtor': SundryDebtor,
        'Loan': Loan,
        'CreditorTransaction': CreditorTransaction,
        'DebtorTransaction': DebtorTransaction,
        'Party': Party,
        'MetalStockType': MetalStockType,
        'GoldSilverPurchase': GoldSilverPurchase,
        'CustomerPurchase': CustomerPurchase,
        'MetalStock': MetalStock,
        'MetalStockMovement': MetalStockMovement,
        'Stock': Stock,
        'DailyRate': DailyRate,
        'Stone': Stone,
        'Motimala': Motimala,
        'Potey': Potey,
        'MainCategory': MainCategory,
        'SubCategory': SubCategory,
        'Kaligar': Kaligar,
        'Ornament': Ornament,
        'Kaligar_Ornaments': Kaligar_Ornaments,
        'Kaligar_CashAccount': Kaligar_CashAccount,
        'Kaligar_GoldAccount': Kaligar_GoldAccount,
        'Order': Order,
        'OrderMetalStock': OrderMetalStock,
        'OrderPayment': OrderPayment,
        'OrderOrnament': OrderOrnament,
        'DebtorPayment': DebtorPayment,
        'Sale': Sale,
        'SalesMetalStock': SalesMetalStock,
    }
    
    if model_name not in model_map:
        return 0, 0, [f"Unknown model: {model_name}"]
    
    # For simplicity, we'll use basic create logic - you can extend this
    # with the detailed import logic from import_all_data function
    
    return count, skipped, errors


def import_model_xlsx(sheet_name, worksheet, skip_existing=True):
    """Import a single model from XLSX sheet."""
    count = 0
    skipped = 0
    errors = []
    
    # Similar to import_model_json but reading from worksheet
    # You can reuse logic from import_all_data function
    
    return count, skipped, errors
