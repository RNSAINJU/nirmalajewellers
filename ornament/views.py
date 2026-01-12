from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from .models import Kaligar, Ornament, MainCategory, SubCategory
from order.models import Order
from .forms import OrnamentForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Q
from io import BytesIO
from django.contrib import messages
from decimal import Decimal
from django.forms import modelformset_factory
import openpyxl
from openpyxl.utils import get_column_letter
import nepali_datetime as ndt
from main.models import Stock

class MainCategoryCreateView(CreateView):
    model = MainCategory
    fields = ['name']
    template_name = 'ornament/maincategory_form.html'
    success_url = reverse_lazy('ornament:list')

class SubCategoryCreateView(CreateView):
    model = SubCategory
    fields = ['name']
    template_name = 'ornament/subcategory_form.html'
    success_url = reverse_lazy('ornament:list')

class KaligarCreateView(CreateView):
    model = Kaligar
    fields = ['name','phone_no','panno','address','stamp']
    template_name = 'ornament/kaligar_form.html'
    success_url = reverse_lazy('ornament:list')


class OrnamentListView(ListView):
    model = Ornament
    template_name = 'ornament/ornament_list.html'
    context_object_name = 'ornaments'
    # Order by latest entry first
    ordering = ['-id']

    def get_queryset(self):
        qs = super().get_queryset()

        # Filters
        code = self.request.GET.get("code")
        name = self.request.GET.get("name")
        customer = self.request.GET.get("customer")
        type = self.request.GET.get("type")
        ornament_type = self.request.GET.get("ornament_type")
        metal_type = self.request.GET.get("metal_type")
        maincategory_id = self.request.GET.get("maincategory")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        kaligar_id = self.request.GET.get('kaligar')
        search=self.request.GET.get('search')

        if search:
            qs = qs.filter(
            Q(weight__icontains=search) |
            Q(diamond_weight__icontains=search) |
            Q(ornament_name__icontains=search) |
            Q(gross_weight__icontains=search)
    )

        if code:
            qs = qs.filter(code__icontains=code)

        if name:
            qs = qs.filter(ornament_name__icontains=name)

        if type:
            qs = qs.filter(type=type)

        if ornament_type:
            qs = qs.filter(ornament_type=ornament_type)

        if metal_type:
            qs = qs.filter(metal_type=metal_type)

        if kaligar_id:
            qs = qs.filter(kaligar_id=kaligar_id)

        if maincategory_id:
            qs = qs.filter(maincategory_id=maincategory_id)

        if start_date and end_date:
            qs = qs.filter(
                ornament_date__gte=start_date,
                ornament_date__lte=end_date
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = context['ornaments']

        # Total weight calculation
        context['total_weight'] = qs.aggregate(total=Sum('weight'))['total'] or 0

        # Ornament counts by metal type - single query with values().annotate()
        metal_counts = Ornament.objects.values('metal_type').annotate(
            count=Sum(1)
        )
        metal_count_dict = {item['metal_type']: item['count'] for item in metal_counts}
        
        context['gold_count'] = metal_count_dict.get('Gold', 0)
        context['silver_count'] = metal_count_dict.get('Silver', 0)
        context['diamond_count'] = metal_count_dict.get('Diamond', 0)
        
        # Diamond total amount calculation
        diamond_ornaments = Ornament.objects.filter(metal_type='Diamond')
        diamond_agg = diamond_ornaments.aggregate(
            diamond_amount=Sum(F('diamond_weight') * F('diamond_rate'), output_field=DecimalField()),
            total_jyala=Sum(F('jyala'), output_field=DecimalField()),
            total_stone=Sum(F('stone_totalprice'), output_field=DecimalField())
        )
        total_diamond_amount = diamond_agg.get('diamond_amount') or 0
        try:
            gold_rate = Stock.objects.get(year=2082).gold_rate
        except Stock.DoesNotExist:
            gold_rate = Decimal('0')
        total_jyala = diamond_agg.get('total_jyala') or 0
        total_stone_amount = diamond_agg.get('total_stone') or 0
        total_gold_amount = diamond_ornaments.aggregate(
            total=Sum((F('weight') * 0.59 )* (gold_rate), output_field=DecimalField())
        )['total'] or 0
        context['diamond_total_amount'] = total_diamond_amount+total_gold_amount+total_jyala+total_stone_amount

        # Gold total amount calculation
        gold_ornaments = Ornament.objects.filter(metal_type='Gold')
        total_gold_ornament_jarti = gold_ornaments.aggregate(
            total=Sum(F('jarti')* gold_rate, output_field=DecimalField())
        )['total'] or 0
        total_gold_ornament_weight = gold_ornaments.aggregate(
            total=Sum('weight')
        )['total'] or 0
        context['gold_total_weight'] = total_gold_ornament_weight
        
        # Gold weight breakdown by individual karat type
        gold_24k_weight = gold_ornaments.filter(type='24KARAT').aggregate(
            total=Sum('weight')
        )['total'] or Decimal('0')
        gold_22k_weight = gold_ornaments.filter(type='22KARAT').aggregate(
            total=Sum('weight')
        )['total'] or Decimal('0')
        gold_18k_weight = gold_ornaments.filter(type='18KARAT').aggregate(
            total=Sum('weight')
        )['total'] or Decimal('0')
        gold_14k_weight = gold_ornaments.filter(type='14KARAT').aggregate(
            total=Sum('weight')
        )['total'] or Decimal('0')
        gold_24k_finalweight= gold_24k_weight + (gold_22k_weight * Decimal('0.92'))+ (gold_18k_weight * Decimal('0.75')) + (gold_14k_weight * Decimal('0.58'))
        total_gold_ornament_amount=gold_24k_finalweight * gold_rate
        context['gold_total_amount'] = total_gold_ornament_amount + total_gold_ornament_jarti
        context['gold_24k_finalweight'] = gold_24k_finalweight
        context['gold_24k_weight'] = gold_24k_weight
        context['gold_22k_weight'] = gold_22k_weight
        context['gold_18k_weight'] = gold_18k_weight
        context['gold_14k_weight'] = gold_14k_weight

        # Filters back to template
        context['metal_type'] = self.request.GET.get('metal_type')
        context['ornament_type'] = self.request.GET.get('ornament_type')
        context['type'] = self.request.GET.get('type')
        context['maincategory'] = self.request.GET.get('maincategory')

        # Kaligar list
        context['kaligar'] = Kaligar.objects.all()
        context['selected_kaligar'] = self.request.GET.get('kaligar', '')

        return context


class OrnamentCreateView(CreateView):
    model = Ornament
    form_class = OrnamentForm
    template_name = 'ornament/ornament_form.html'
    success_url = reverse_lazy('ornament:list')

    def get_initial(self):
        """Set initial values including today's Nepali date."""
        initial = super().get_initial()
        initial['ornament_date'] = ndt.date.today()
        # Set default values for weight fields
        initial['gross_weight'] = Decimal('0.0')
        initial['weight'] = Decimal('0.0')
        initial['diamond_weight'] = Decimal('0.0')
        initial['diamond_rate'] = Decimal('0.0')
        initial['zircon_weight'] = Decimal('0.0')
        initial['stone_weight'] = Decimal('0.0')
        initial['stone_percaratprice'] = Decimal('0.0')
        initial['stone_totalprice'] = Decimal('0.0')
        initial['jarti'] = Decimal('0.0')
        initial['jyala'] = Decimal('0.0')
        return initial

    def form_valid(self, form):
        # Cloudinary image is automatically handled by ModelForm
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['JARTI_CHOICES'] = [
            (4.0, "4%"),
            (4.5, "4.5%"),
            (5.0, "5%"),
            (6.5, "6.5%"),
            (8.0, "8%"),
        ]
        return context


class OrnamentUpdateView(UpdateView):
    model = Ornament
    form_class = OrnamentForm
    template_name = 'ornament/ornament_form.html'
    success_url = reverse_lazy('ornament:list')

    def form_valid(self, form):
        # Cloudinary image is automatically handled by ModelForm
        return super().form_valid(form)

    def get_success_url(self):
        # Check if there's a 'next' parameter to redirect back to
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return self.success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['JARTI_CHOICES'] = [
            (4.0, "4%"),
            (4.5, "4.5%"),
            (5.0, "5%"),
            (6.5, "6.5%"),
            (8.0, "8%"),
        ]
        return context


class OrnamentDeleteView(DeleteView):
    model = Ornament
    template_name = 'ornament/ornament_confirm_delete.html'
    success_url = reverse_lazy('ornament:list')


class OrnamentDestroyView(UpdateView):
    """Change ornament status to 'destroyed'."""
    model = Ornament
    fields = []
    template_name = 'ornament/ornament_confirm_destroy.html'
    success_url = reverse_lazy('ornament:list')

    def form_valid(self, form):
        """Update status to destroyed."""
        self.object.status = Ornament.StatusCategory.DESTROYED
        self.object.save()
        messages.success(self.request, f"Ornament '{self.object.ornament_name}' marked as destroyed.")
        return super().form_valid(form)


def multiple_ornament_create(request):
    """Create multiple ornaments at once using a model formset.

    This provides a separate page where you can enter several ornaments in
    one go, similar in spirit to the order create page.
    """

    OrnamentFormSet = modelformset_factory(
        Ornament,
        form=OrnamentForm,
        extra=5,
        can_delete=False,
    )

    if request.method == "POST":
        formset = OrnamentFormSet(request.POST, request.FILES, queryset=Ornament.objects.none())
        if formset.is_valid():
            formset.save()
            return redirect('ornament:list')
    else:
        formset = OrnamentFormSet(queryset=Ornament.objects.none())

    return render(request, 'ornament/ornament_bulk_form.html', {
        'formset': formset,
    })


def print_view(request):
    ornament = Ornament.objects.filter(id__gte=1).order_by('id')

    total_weight = ornament.aggregate(
        total=Sum('weight')
    )['total'] or 0

    return render(request, "ornament/print_view.html", {
        "ornament": ornament,
        "total_weight": total_weight
    })


def export_excel(request):
    view = OrnamentListView()
    view.request = request  # attach request
    ornaments = view.get_queryset()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ornaments"

    headers = [
        "Ornament Date", "Code", "Metal Type","Type", "Ornament Type",
        "MainCategory", "SubCategory", "Ornament Name","Gross Weight",
        "Weight", "Diamond/Stones Weight","Diamond Rate","Zircon Weight","Stone Weight",
        "Stone Price Per Carat","Stone Total Price",
        "Jarti","Jyala","Kaligar","Description","Image","Order","Created at","Updated at","Status"
    ]
    ws.append(headers)

    for o in ornaments:
        ws.append([
            str(o.ornament_date),
            o.code,
            o.metal_type,
            o.type,
            o.ornament_type,
            o.maincategory.name if o.maincategory else "",
            o.subcategory.name if o.subcategory else "",
            o.ornament_name,
            o.gross_weight,
            o.weight,
            o.diamond_weight,
            o.diamond_rate,
            o.zircon_weight,
            o.stone_weight,
            o.stone_percaratprice,
            o.stone_totalprice,
            o.jarti,
            o.jyala,
            o.kaligar.name if o.kaligar else "",
            o.description if o.description else "",
            str(o.image) if o.image else "",
            str(o.order) if o.order else "",
            str(o.created_at),
            str(o.updated_at),
            "fetched"
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
    response['Content-Disposition'] = 'attachment; filename="ornaments.xlsx"'

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
            return redirect("ornament:import_excel")

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
                        ornament_date_bs,
                        code,
                        metal_type,
                        type,
                        ornament_type,
                        maincategory_name,
                        subcategory_name,
                        ornament_name,
                        gross_weight,
                        weight,
                        diamond_weight,
                        diamond_rate,
                        zircon_weight,
                        stone_weight,
                        stone_percaratprice,
                        stone_totalprice,
                        jarti,
                        jyala,
                        kaligar_name,
                        description,
                        image,
                        order,
                        created_at,
                        updated_at,
                        status
                    ) = row
                except Exception:
                    messages.error(request, "Excel format is incorrect. Columns mismatch.")
                    return redirect("ornament:import_excel")

                # =============== 1️⃣ Status  Check if it already fetched===============
                if status == "fetched":
                    skipped += 1
                    continue


                # =============== 1️⃣ Duplicate Bill Check ===============
                if Ornament.objects.filter(code=str(code)).exists():
                    skipped += 1
                    continue

                # =============== 2️⃣ Find/Create Main Category ===============
                maincategory = None

                if maincategory_name:
                    maincategory = MainCategory.objects.filter(name=str(maincategory_name)).first()

                if not maincategory:
                    maincategory = MainCategory.objects.create(
                        name=maincategory_name or "Unknown"
                    )

                # =============== 2️⃣ Find/Create Sub Category ===============
                subcategory = None

                if subcategory_name:
                    subcategory = SubCategory.objects.filter(name=str(subcategory_name)).first()

                if not subcategory:
                    subcategory = SubCategory.objects.create(
                        name=subcategory_name or "Unknown",
                    )

                # =============== 2️⃣ Find/Create Kaligar ===============
                kaligar = None

                if kaligar_name:
                    kaligar = Kaligar.objects.filter(name=str(kaligar_name)).first()

                if not kaligar:
                    kaligar = Kaligar.objects.create(
                        name=kaligar_name or "Unknown",
                        phone_no="",
                        panno=123456789,
                        address="",
                        stamp=""
                    )

                # =============== 2️⃣ Find Order by reference (from export column) ===============
                linked_order = None
                if order:
                    # Try direct numeric sn
                    try:
                        linked_order = Order.objects.filter(sn=int(str(order).strip())).first()
                    except Exception:
                        linked_order = None

                    # Fallback: extract first integer from string like "Order 3 - Customer"
                    if linked_order is None:
                        import re
                        match = re.search(r"(\d+)", str(order))
                        if match:
                            try:
                                sn_val = int(match.group(1))
                                linked_order = Order.objects.filter(sn=sn_val).first()
                            except Exception:
                                linked_order = None

                # if not order:
                #     kaligar = Kaligar.objects.create(
                #         name=kaligar_name or "Unknown",
                #     )

                # =============== 3️⃣ Convert BS Date ===============
                try:
                    y, m, d = map(int, str(ornament_date_bs).split("-"))
                    ornament_date = ndt.date(y, m, d)
                except:
                    ornament_date = ndt.date.today()

                # =============== 4️⃣ Convert all decimals safely ===============
                gross_weight = to_decimal(gross_weight)
                weight = to_decimal(weight)
                diamond_weight = to_decimal(diamond_weight)
                diamond_rate = to_decimal(diamond_rate)
                zircon_weight = to_decimal(zircon_weight)
                stone_weight = to_decimal(stone_weight)
                stone_percaratprice = to_decimal(stone_percaratprice)
                stone_totalprice = to_decimal(stone_totalprice)
                jarti = to_decimal(jarti)
                jyala = to_decimal(jyala)

                # =============== 5️⃣ Create Purchase ===============
                Ornament.objects.create(
                    ornament_date=str(ornament_date),
                    code=code,
                    metal_type=metal_type,
                    type=type,
                    ornament_type=ornament_type,
                    maincategory=maincategory,
                    subcategory=subcategory,
                    ornament_name=ornament_name,
                    gross_weight=gross_weight,
                    weight = weight,
                    diamond_weight = diamond_weight,
                    diamond_rate = diamond_rate,
                    zircon_weight=zircon_weight,
                    stone_weight=stone_weight,
                    stone_percaratprice=stone_percaratprice,
                    stone_totalprice=stone_totalprice,
                    jarti=jarti,
                    jyala=jyala,
                    kaligar=kaligar,
                    description=description,
                    image=image,
                    order=linked_order,
                    created_at=created_at,
                    updated_at=updated_at,
                )

                imported += 1

            messages.success(
                request,
                f"Imported: {imported} | Skipped duplicates: {skipped}"
            )
            return redirect("ornament:list")

        except Exception as e:
            messages.error(request, f"Error while importing: {e}")
            return redirect("ornament:import_excel")

    return render(request, "ornament/import_excel.html")


def ornament_report(request):
    """Show ornament counts grouped by metal type, then by main category."""
    from django.db.models import Count

    total_ornaments = Ornament.objects.filter(
        ornament_type__in=[
            Ornament.OrnamentCategory.STOCK,
            Ornament.OrnamentCategory.ORDER,
        ]
    ).count()

    # Totals per metal type
    metal_totals = {
        row['metal_type']: row['count']
        for row in Ornament.objects.filter(
            ornament_type__in=[
                Ornament.OrnamentCategory.STOCK,
                Ornament.OrnamentCategory.ORDER,
            ]
        ).values('metal_type').annotate(count=Count('id'))
    }

    # Category breakdown per metal
    category_rows = (
        Ornament.objects.filter(
            ornament_type__in=[
                Ornament.OrnamentCategory.STOCK,
                Ornament.OrnamentCategory.ORDER,
            ]
        )
        .values('metal_type', 'maincategory__id', 'maincategory__name')
        .annotate(count=Count('id'))
        .order_by('metal_type', 'maincategory__name')
    )

    metal_order = ['Diamond', 'Gold', 'Silver', 'Others']
    sections = []

    for metal in metal_order:
        total = metal_totals.get(metal, 0)
        if total == 0:
            continue

        categories = [
            {
                'id': row['maincategory__id'],
                'name': row['maincategory__name'] or 'Uncategorized',
                'count': row['count'],
            }
            for row in category_rows
            if row['metal_type'] == metal
        ]

        sections.append({
            'metal': metal,
            'total': total,
            'categories': categories,
        })

    context = {
        'sections': sections,
        'total_ornaments': total_ornaments,
    }
    return render(request, 'ornament/ornament_report.html', context)


def ornament_weight_report(request):
    """Show ornament total net weight by metal type."""
    from django.db.models import F, Case, When, Value
    
    # Get total weight grouped by metal type
    weight_by_metal = Ornament.objects.filter(
        ornament_type=Ornament.OrnamentCategory.STOCK
    ).values('metal_type').annotate(
        total_weight=Sum('weight'),
        total_gross_weight=Sum('gross_weight'),
        total_jarti=Sum('jarti'),
        total_jyala=Sum('jyala'),
        ornament_count=Sum(1)
    ).order_by('metal_type')
    
    # Get latest gold rate for calculations
    try:
        latest_rate = Stock.objects.latest('year')
        gold_rate = latest_rate.gold_rate
        silver_rate = latest_rate.silver_rate
    except Stock.DoesNotExist:
        gold_rate = Decimal('0')
        silver_rate = Decimal('0')
    
    # Track grand total amount across all metal types
    grand_total_amount = Decimal('0')
    
    # Pre-fetch all karat breakdowns in a single query per metal type
    gold_ornaments = Ornament.objects.filter(
        metal_type='Gold',
        ornament_type=Ornament.OrnamentCategory.STOCK,
    )
    
    silver_ornaments = Ornament.objects.filter(
        metal_type='Silver',
        ornament_type=Ornament.OrnamentCategory.STOCK,
    )
    
    diamond_ornaments = Ornament.objects.filter(
        metal_type='Diamond',
        ornament_type=Ornament.OrnamentCategory.STOCK,
    )
    
    # Enrich metal data with karat breakdown and total amount
    for metal in weight_by_metal:
        if metal['metal_type'] == 'Gold':
            # Get all karat breakdown data in one query
            karat_data = gold_ornaments.values('type').annotate(
                weight_sum=Sum('weight'),
                stone_sum=Sum('stone_totalprice')
            )
            
            karat_dict = {item['type']: item for item in karat_data}
            
            gold_24k = karat_dict.get('24KARAT', {}).get('weight_sum') or Decimal('0')
            gold_22k = karat_dict.get('22KARAT', {}).get('weight_sum') or Decimal('0')
            gold_18k = karat_dict.get('18KARAT', {}).get('weight_sum') or Decimal('0')
            gold_14k = karat_dict.get('14KARAT', {}).get('weight_sum') or Decimal('0')
            
            # Calculate total amount in 24k equivalent
            gold_24k_equivalent = (
                gold_24k + 
                (gold_22k * Decimal('0.92')) + 
                (gold_18k * Decimal('0.75')) + 
                (gold_14k * Decimal('0.58'))
            )
            
            # Get total jarti and jyala for gold
            total_jarti = metal['total_jarti'] or Decimal('0')
            total_jyala = metal['total_jyala'] or Decimal('0')
            
            # Get total stone price for gold
            total_stone_price = gold_ornaments.aggregate(
                total=Sum(F('stone_totalprice'), output_field=DecimalField())
            )['total'] or Decimal('0')
            
            # Calculate component amounts
            gold_amount = gold_24k_equivalent * gold_rate
            jarti_amount = total_jarti * gold_rate
            
            # Calculate total amount: ((24k gold + jarti) * rate) + jyala + stone_totalprice
            total_amount = gold_amount + jarti_amount + total_jyala + total_stone_price
            
            metal['gold_24k'] = gold_24k
            metal['gold_22k'] = gold_22k
            metal['gold_18k'] = gold_18k
            metal['gold_14k'] = gold_14k
            metal['gold_24k_equivalent'] = gold_24k_equivalent
            metal['gold_amount'] = gold_amount
            metal['jarti_amount'] = jarti_amount
            metal['jyala_amount'] = total_jyala
            metal['stone_amount'] = total_stone_price
            metal['total_amount'] = total_amount
            
            # Add to grand total
            grand_total_amount += total_amount
            
        elif metal['metal_type'] == 'Silver':
            # Get all karat breakdown data in one query
            karat_data = silver_ornaments.values('type').annotate(
                weight_sum=Sum('weight'),
                stone_sum=Sum('stone_totalprice')
            )
            
            karat_dict = {item['type']: item for item in karat_data}
            
            silver_24k = karat_dict.get('24KARAT', {}).get('weight_sum') or Decimal('0')
            silver_22k = karat_dict.get('22KARAT', {}).get('weight_sum') or Decimal('0')
            silver_18k = karat_dict.get('18KARAT', {}).get('weight_sum') or Decimal('0')
            silver_14k = karat_dict.get('14KARAT', {}).get('weight_sum') or Decimal('0')
            
            # Calculate total amount in 24k equivalent
            silver_24k_equivalent = (
                silver_24k + 
                (silver_22k * Decimal('0.92')) + 
                (silver_18k * Decimal('0.75')) + 
                (silver_14k * Decimal('0.58'))
            )
            
            # Get total jarti and jyala for silver
            total_jarti = metal['total_jarti'] or Decimal('0')
            total_jyala = metal['total_jyala'] or Decimal('0')
            
            # Get total stone price for silver
            total_stone_price = silver_ornaments.aggregate(
                total=Sum(F('stone_totalprice'), output_field=DecimalField())
            )['total'] or Decimal('0')
            
            # Calculate component amounts
            silver_amount = silver_24k_equivalent * silver_rate
            jarti_amount = total_jarti * silver_rate
            
            # Calculate total amount: ((24k silver + jarti) * rate) + jyala + stone_totalprice
            total_amount = silver_amount + jarti_amount + total_jyala + total_stone_price
            
            metal['silver_24k'] = silver_24k
            metal['silver_22k'] = silver_22k
            metal['silver_18k'] = silver_18k
            metal['silver_14k'] = silver_14k
            metal['silver_24k_equivalent'] = silver_24k_equivalent
            metal['silver_amount'] = silver_amount
            metal['jarti_amount'] = jarti_amount
            metal['jyala_amount'] = total_jyala
            metal['stone_amount'] = total_stone_price
            metal['total_amount'] = total_amount
            
            # Add to grand total
            grand_total_amount += total_amount
            
        elif metal['metal_type'] == 'Diamond':
            # Calculate diamond total amount with proper karat conversion
            # Get all karat breakdown data in one query
            karat_data = diamond_ornaments.values('type').annotate(
                weight_sum=Sum('weight')
            )
            
            karat_dict = {item['type']: item for item in karat_data}
            
            diamond_24k = karat_dict.get('24KARAT', {}).get('weight_sum') or Decimal('0')
            diamond_22k = karat_dict.get('22KARAT', {}).get('weight_sum') or Decimal('0')
            diamond_18k = karat_dict.get('18KARAT', {}).get('weight_sum') or Decimal('0')
            diamond_14k = karat_dict.get('14KARAT', {}).get('weight_sum') or Decimal('0')
            
            # Convert to 24k equivalent for diamond gold content
            diamond_24k_equivalent = (
                diamond_24k + 
                (diamond_22k * Decimal('0.92')) + 
                (diamond_18k * Decimal('0.75')) + 
                (diamond_14k * Decimal('0.58'))
            )
            
            # Gold amount (24k equivalent * gold rate)
            total_gold_amount = diamond_24k_equivalent * gold_rate
            
            # Get all aggregated data in one query
            diamond_agg = diamond_ornaments.aggregate(
                diamond_amount=Sum(F('diamond_weight') * F('diamond_rate'), output_field=DecimalField()),
                total_jyala=Sum(F('jyala'), output_field=DecimalField()),
                total_stone=Sum(F('stone_totalprice'), output_field=DecimalField())
            )
            
            total_diamond_amount = diamond_agg.get('diamond_amount') or Decimal('0')
            total_jyala = diamond_agg.get('total_jyala') or Decimal('0')
            total_stone_amount = diamond_agg.get('total_stone') or Decimal('0')
            
            # Jarti amount (jarti * gold rate)
            total_jarti_amount = (metal['total_jarti'] or Decimal('0')) * gold_rate
            
            # Total = (24k gold * rate) + (diamond_weight * diamond_rate) + jyala + (jarti * rate) + stone_totalprice
            total_amount = total_gold_amount + total_diamond_amount + total_jyala + total_jarti_amount + total_stone_amount
            
            metal['diamond_24k'] = diamond_24k
            metal['diamond_22k'] = diamond_22k
            metal['diamond_18k'] = diamond_18k
            metal['diamond_14k'] = diamond_14k
            metal['diamond_24k_equivalent'] = diamond_24k_equivalent
            metal['gold_amount'] = total_gold_amount
            metal['diamond_weight_amount'] = total_diamond_amount
            metal['jarti_amount'] = total_jarti_amount
            metal['jyala_amount'] = total_jyala
            metal['stone_amount'] = total_stone_amount
            metal['total_amount'] = total_amount
            
            # Add to grand total
            grand_total_amount += total_amount
        else:
            # For other metal types, set to 0
            metal['total_amount'] = Decimal('0')
    
    # Calculate overall totals
    totals = Ornament.objects.filter(
        ornament_type=Ornament.OrnamentCategory.STOCK
    ).aggregate(
        total_weight=Sum('weight'),
        total_gross_weight=Sum('gross_weight'),
        total_jarti=Sum('jarti'),
        total_jyala=Sum('jyala'),
        total_count=Sum(1)
    )
    
    # Calculate total 24k equivalent gold across all ornaments
    gold_ornaments = Ornament.objects.filter(
        metal_type='Gold',
        ornament_type=Ornament.OrnamentCategory.STOCK,
    )
    
    gold_24k_total = gold_ornaments.filter(type='24KARAT').aggregate(
        total=Sum('weight')
    )['total'] or Decimal('0')
    
    gold_22k_total = gold_ornaments.filter(type='22KARAT').aggregate(
        total=Sum('weight')
    )['total'] or Decimal('0')
    
    gold_18k_total = gold_ornaments.filter(type='18KARAT').aggregate(
        total=Sum('weight')
    )['total'] or Decimal('0')
    
    gold_14k_total = gold_ornaments.filter(type='14KARAT').aggregate(
        total=Sum('weight')
    )['total'] or Decimal('0')
    
    # Calculate 24k equivalent
    total_24k_equivalent = (
        gold_24k_total + 
        (gold_22k_total * Decimal('0.92')) + 
        (gold_18k_total * Decimal('0.75')) + 
        (gold_14k_total * Decimal('0.58'))
    )
    
    context = {
        'weight_by_metal': weight_by_metal,
        'totals': totals,
        'gold_rate': gold_rate,
        'grand_total_amount': grand_total_amount,
        'total_24k_equivalent': total_24k_equivalent,
    }
    return render(request, 'ornament/ornament_weight_report.html', context)


def rates_and_stock_view(request):
    """View to display fetched rates and stock year rates with dropdown."""
    from main.models import DailyRate
    
    # Get selected rate date and stock year from request
    selected_rate_date = request.GET.get('rate_date')
    selected_stock_year = request.GET.get('stock_year')
    
    # Get all daily rates (fetched rates)
    daily_rates = DailyRate.objects.all().order_by('-date')
    
    # Get all stock years from both ornament and main app Stock models
    stock_years = Stock.objects.all().order_by('-year')
    
    # Initialize selected rate and stock data
    selected_rate = None
    selected_stock = None
    
    if selected_rate_date:
        try:
            selected_rate = DailyRate.objects.get(date=selected_rate_date)
        except DailyRate.DoesNotExist:
            pass
    else:
        # Show the most recent rate by default
        selected_rate = daily_rates.first()
    
    if selected_stock_year:
        try:
            selected_stock = Stock.objects.get(year=selected_stock_year)
        except Stock.DoesNotExist:
            pass
    else:
        # Show the most recent stock year by default
        selected_stock = stock_years.first()
    
    # Calculate amounts for selected stock
    stock_amounts = {}
    if selected_stock:
        stock_amounts = {
            'diamond_amount': selected_stock.diamond_amount,
            'gold_amount': selected_stock.gold_amount,
            'silver_amount': selected_stock.silver_amount,
        }
    
    context = {
        'daily_rates': daily_rates,
        'stock_years': stock_years,
        'selected_rate': selected_rate,
        'selected_stock': selected_stock,
        'stock_amounts': stock_amounts,
        'selected_rate_date': selected_rate_date,
        'selected_stock_year': selected_stock_year,
    }
    
    return render(request, 'ornament/rates_and_stock.html', context)


def kaligar_list(request):
    """Display list of all kaligar with their ornament weights."""
    from django.db.models import Sum, DecimalField
    from django.db.models.functions import Coalesce
    from decimal import Decimal
    
    # Get all kaligar
    kaligars = Kaligar.objects.all().order_by('name')
    
    # Get selected kaligar if filtering
    selected_kaligar_id = request.GET.get('kaligar_id')
    selected_kaligar = None
    selected_kaligar_ornaments = None
    ornaments_by_metal_type = {}
    metal_type_totals = {}
    overall_totals = {
        'weight': Decimal('0'),
        'jarti': Decimal('0'),
        'jyala': Decimal('0'),
        'gross_weight': Decimal('0'),
        'diamond_weight': Decimal('0'),
        'zircon_weight': Decimal('0'),
        'stone_weight': Decimal('0'),
        'stone_totalprice': Decimal('0'),
    }
    
    if selected_kaligar_id:
        try:
            selected_kaligar = Kaligar.objects.get(id=selected_kaligar_id)
            all_ornaments = selected_kaligar.ornaments.all().order_by('-ornament_date')
            # Group ornaments by metal type and calculate totals
            for ornament in all_ornaments:
                metal_type = ornament.get_metal_type_display()
                if metal_type not in ornaments_by_metal_type:
                    ornaments_by_metal_type[metal_type] = []
                    metal_type_totals[metal_type] = {
                        'weight': Decimal('0'),
                        'jarti': Decimal('0'),
                        'jyala': Decimal('0'),
                        'gross_weight': Decimal('0'),
                        'diamond_weight': Decimal('0'),
                        'zircon_weight': Decimal('0'),
                        'stone_weight': Decimal('0'),
                        'stone_totalprice': Decimal('0'),
                    }
                ornaments_by_metal_type[metal_type].append(ornament)
                
                # Add to metal type totals
                metal_type_totals[metal_type]['weight'] += ornament.weight or Decimal('0')
                metal_type_totals[metal_type]['jarti'] += ornament.jarti or Decimal('0')
                metal_type_totals[metal_type]['jyala'] += ornament.jyala or Decimal('0')
                metal_type_totals[metal_type]['gross_weight'] += ornament.gross_weight or Decimal('0')
                metal_type_totals[metal_type]['diamond_weight'] += ornament.diamond_weight or Decimal('0')
                metal_type_totals[metal_type]['zircon_weight'] += ornament.zircon_weight or Decimal('0')
                metal_type_totals[metal_type]['stone_weight'] += ornament.stone_weight or Decimal('0')
                metal_type_totals[metal_type]['stone_totalprice'] += ornament.stone_totalprice or Decimal('0')
                
                # Add to overall totals
                overall_totals['weight'] += ornament.weight or Decimal('0')
                overall_totals['jarti'] += ornament.jarti or Decimal('0')
                overall_totals['jyala'] += ornament.jyala or Decimal('0')
                overall_totals['gross_weight'] += ornament.gross_weight or Decimal('0')
                overall_totals['diamond_weight'] += ornament.diamond_weight or Decimal('0')
                overall_totals['zircon_weight'] += ornament.zircon_weight or Decimal('0')
                overall_totals['stone_weight'] += ornament.stone_weight or Decimal('0')
                overall_totals['stone_totalprice'] += ornament.stone_totalprice or Decimal('0')
        except Kaligar.DoesNotExist:
            pass
    
    # Annotate each kaligar with total ornament weight
    kaligars_with_weights = []
    total_ornament_count = 0
    for kaligar in kaligars:
        total_weight = kaligar.ornaments.aggregate(
            total=Coalesce(Sum('weight'), Decimal('0'), output_field=DecimalField())
        )['total']
        ornament_count = kaligar.ornaments.count()
        total_ornament_count += ornament_count
        kaligars_with_weights.append({
            'id': kaligar.id,
            'name': kaligar.name,
            'phone_no': kaligar.phone_no,
            'panno': kaligar.panno,
            'address': kaligar.address,
            'total_weight': total_weight,
            'ornament_count': ornament_count
        })
    
    context = {
        'kaligars': kaligars_with_weights,
        'selected_kaligar': selected_kaligar,
        'selected_kaligar_ornaments': selected_kaligar_ornaments,
        'ornaments_by_metal_type': ornaments_by_metal_type,
        'metal_type_totals': metal_type_totals,
        'overall_totals': overall_totals,
        'total_ornament_count': total_ornament_count,
    }
    
    return render(request, 'ornament/kaligar_list.html', context)
