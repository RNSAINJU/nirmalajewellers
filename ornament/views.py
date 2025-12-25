from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Sum
from .models import Kaligar, Ornament, MainCategory, SubCategory
from .forms import OrnamentForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Q
from io import BytesIO
from django.contrib import messages
from decimal import Decimal
from django.forms import modelformset_factory
# import openpyxl
# from openpyxl.utils import get_column_letter
import nepali_datetime as ndt

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
    # Order serially by primary key (id)
    ordering = ['id']

    def get_queryset(self):
        qs = super().get_queryset()

        # Filters
        code = self.request.GET.get("code")
        name = self.request.GET.get("name")
        customer = self.request.GET.get("customer")
        type = self.request.GET.get("type")
        ornament_type = self.request.GET.get("ornament_type")
        metal_type = self.request.GET.get("metal_type")
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

        # Ornament counts by metal type
        context['gold_count'] = Ornament.objects.filter(metal_type__icontains='Gold').count()
        context['silver_count'] = Ornament.objects.filter(metal_type__icontains='Silver').count()
        context['diamond_count'] = Ornament.objects.filter(metal_type__icontains='Diamond').count()

        # Filters back to template
        context['metal_type'] = self.request.GET.get('metal_type')
        context['ornament_type'] = self.request.GET.get('ornament_type')
        context['type'] = self.request.GET.get('type')

        # Kaligar list
        context['kaligar'] = Kaligar.objects.all()
        context['selected_kaligar'] = self.request.GET.get('kaligar', '')

        return context


class OrnamentCreateView(CreateView):
    model = Ornament
    form_class = OrnamentForm
    template_name = 'ornament/ornament_form.html'
    success_url = reverse_lazy('ornament:list')

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
        "Weight", "Diamond/Stones Weight","Zircon Weight","Stone Weight",
        "Stone Price Per Carat","Stone Total Price",
        "Jarti","Jyala","Kaligar","Image","Order","Created at","Updated at","Status"
    ]
    ws.append(headers)

    for o in ornaments:
        ws.append([
            str(o.ornament_date),
            o.code,
            o.metal_type,
            o.type,
            o.ornament_type,
            o.maincategory.name,
            o.subcategory.name,
            o.ornament_name,
            o.gross_weight,
            o.weight,
            o.diamond_weight,
            o.zircon_weight,
            o.stone_weight,
            o.stone_percaratprice,
            o.stone_totalprice,
            o.jarti,
            o.jyala,
            o.kaligar.name,
            str(o.image) if o.image else "",   # ★ convert Cloudinary resource to URL
            o.order,
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
                        zircon_weight,
                        stone_weight,
                        stone_percaratprice,
                        stone_totalprice,
                        jarti,
                        jyala,
                        kaligar_name,
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

                # =============== 2️⃣ Find/Create Order ===============
                Order = None

                if order:
                    Order = Order.objects.filter(name=str(order)).first()

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
                    gross_weight= to_decimal(gross_weight),
                    weight = to_decimal(weight),
                    diamond_weight = to_decimal(diamond_weight),
                    zircon_weight = to_decimal(zircon_weight),
                    stone_weight    = to_decimal(stone_weight),
                    stone_percaratprice= to_decimal(stone_percaratprice),    
                    stone_totalprice=to_decimal(stone_totalprice),
                    jarti=to_decimal(jarti)
                    jyala=to_decimal(jyala)
                    

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
                    zircon_weight=zircon_weight,
                    stone_weight=stone_weight,
                    stone_percaratprice=stone_percaratprice,
                    stone_totalprice=stone_totalprice,
                    jarti=jarti,
                    jyala=jyala,
                    kaligar=kaligar,
                    image=image,
                    order=Order,
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
