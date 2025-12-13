from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import GoldSilverPurchase, Party
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
    success_url = reverse_lazy('gsp:list')


class PurchaseCreateView(CreateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party',
        'particular', 'metal_type', 'quantity',
        'rate', 'wages', 'discount','amount', 'payment_mode'
    ]
    template_name = 'goldsilverpurchase/purchase_form.html'
    success_url = reverse_lazy('gsp:list')


class PurchaseUpdateView(UpdateView):
    model = GoldSilverPurchase
    fields = [
        'bill_no', 'bill_date', 'party',
        'particular', 'metal_type', 'quantity',
        'rate', 'wages','discount', 'amount', 'payment_mode'
    ]
    template_name = 'goldsilverpurchase/purchase_form.html'
    success_url = reverse_lazy('gsp:list')


class PurchaseDeleteView(DeleteView):
    model = GoldSilverPurchase
    template_name = 'goldsilverpurchase/purchase_confirm_delete.html'
    success_url = reverse_lazy('gsp:list')



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
        "Particular", "Qty", "Rate", "Wages", "Amount", "Payment"
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
            p.amount,
            p.get_payment_mode_display()
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
                )

                imported += 1

            messages.success(
                request,
                f"Imported: {imported} | Skipped duplicates: {skipped}"
            )
            return redirect("gsp:list")

        except Exception as e:
            messages.error(request, f"Error while importing: {e}")
            return redirect("gsp:gsp_import_excel")

    return render(request, "goldsilverpurchase/import_excel.html")