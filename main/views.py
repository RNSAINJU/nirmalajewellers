from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
import nepali_datetime as ndt

from ornament.models import Ornament, Kaligar
from goldsilverpurchase.models import GoldSilverPurchase, Party
from order.models import Order

# Create your views here.

def index(request):
    return HttpResponse("Hello, Django on Ubuntu!")


def dashboard(request):
    """Dashboard with basic counts and totals across apps."""
    total_ornaments = Ornament.objects.count()
    total_orders = Order.objects.count()
    total_purchase_amount = GoldSilverPurchase.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_order_amount = Order.objects.aggregate(total=Sum('total'))['total'] or 0

    # Stock report by metal type (only STOCK ornaments, summing metal weight)
    stock_qs = Ornament.objects.filter(ornament_type=Ornament.OrnamentCategory.STOCK)
    gold_stock = stock_qs.filter(metal_type=Ornament.MetalTypeCategory.GOLD).aggregate(total=Sum('weight'))['total'] or 0
    silver_stock = stock_qs.filter(metal_type=Ornament.MetalTypeCategory.SILVER).aggregate(total=Sum('weight'))['total'] or 0
    diamond_stock = stock_qs.filter(metal_type=Ornament.MetalTypeCategory.DIAMOND).aggregate(total=Sum('weight'))['total'] or 0

    context = {
        'total_ornaments': total_ornaments,
        'total_orders': total_orders,
        'total_purchase_amount': total_purchase_amount,
        'total_order_amount': total_order_amount,
        'gold_stock': gold_stock,
        'silver_stock': silver_stock,
        'diamond_stock': diamond_stock,
    }
    return render(request, 'main/dashboard.html', context)


def monthly_stock_report(request):
    """Monthly stock report aggregated by month (BS), not by party.

    The underlying date fields (bill_date, order_date) are NepaliDateField,
    so month/year filters operate in Bikram Sambat. This view computes
    totals for the selected BS month and year.
    """

    # Nepali month names (BS)
    NEPALI_MONTHS = {
        1: "Baisakh",
        2: "Jestha",
        3: "Ashar",
        4: "Shrawan",
        5: "Bhadra",
        6: "Ashoj",
        7: "Kartik",
        8: "Manghsir",
        9: "Poush",
        10: "Magh",
        11: "Falgun",
        12: "Chaitra",
    }

    # Optional BS date range (YYYY-MM-DD) to narrow within a month
    from_date_str = request.GET.get("from_date") or ""
    to_date_str = request.GET.get("to_date") or ""

    from_date = None
    to_date = None
    if from_date_str:
        try:
            y, m, d = map(int, from_date_str.split("-"))
            from_date = ndt.date(y, m, d)
        except Exception:
            from_date = None
    if to_date_str:
        try:
            y, m, d = map(int, to_date_str.split("-"))
            to_date = ndt.date(y, m, d)
        except Exception:
            to_date = None

    # Get selected month/year (BS) or default to the most recent data month
    month_param = request.GET.get("month")
    year_param = request.GET.get("year")

    if month_param and year_param:
        month = int(month_param)
        year = int(year_param)
    else:
        reference_date = None
        latest_purchase = (
            GoldSilverPurchase.objects.exclude(bill_date__isnull=True)
            .order_by("-bill_date")
            .first()
        )
        if latest_purchase and latest_purchase.bill_date:
            reference_date = latest_purchase.bill_date

        latest_order = (
            Order.objects.exclude(order_date__isnull=True)
            .order_by("-order_date")
            .first()
        )
        if latest_order and latest_order.order_date:
            if reference_date is None or latest_order.order_date > reference_date:
                reference_date = latest_order.order_date

        if reference_date is not None:
            # NepaliDateField exposes .month/.year in BS
            month = int(reference_date.month)
            year = int(reference_date.year)
        else:
            # Sensible BS fallback if no data exists yet
            month = 1
            year = datetime.now().year

    # Global totals for the selected BS month/year
    totals = {
        "gold_purchase_amount": 0,
        "silver_purchase_amount": 0,
        "customer_amount": 0,
        "sales_amount": 0,
        "gold_purchase_weight": 0,
        "silver_purchase_weight": 0,
        "sales_weight": 0,
        "gold_stock_amount": 0,
        "silver_stock_amount": 0,
        "gold_stock_weight": 0,
        "silver_stock_weight": 0,
    }

    # Gold purchases (all parties) for the chosen BS period
    # Use case-insensitive containment to tolerate imported values like 'Gold', ' GOLD ', etc.
    gold_qs = GoldSilverPurchase.objects.filter(metal_type__icontains="gold")
    if from_date or to_date:
        if from_date:
            gold_qs = gold_qs.filter(bill_date__gte=from_date)
        if to_date:
            gold_qs = gold_qs.filter(bill_date__lte=to_date)
    else:
        gold_qs = gold_qs.filter(bill_date__month=month, bill_date__year=year)
    gold_purchases = gold_qs.aggregate(total_amount=Sum("amount"), total_qty=Sum("quantity"))
    totals["gold_purchase_amount"] = gold_purchases.get("total_amount") or 0
    totals["gold_purchase_weight"] = gold_purchases.get("total_qty") or 0

    # Silver purchases (all parties) for the chosen BS period
    silver_qs = GoldSilverPurchase.objects.filter(metal_type__icontains="silver")
    if from_date or to_date:
        if from_date:
            silver_qs = silver_qs.filter(bill_date__gte=from_date)
        if to_date:
            silver_qs = silver_qs.filter(bill_date__lte=to_date)
    else:
        silver_qs = silver_qs.filter(bill_date__month=month, bill_date__year=year)
    silver_purchases = silver_qs.aggregate(total_amount=Sum("amount"), total_qty=Sum("quantity"))
    totals["silver_purchase_amount"] = silver_purchases.get("total_amount") or 0
    totals["silver_purchase_weight"] = silver_purchases.get("total_qty") or 0

    # Customer sales (orders) for the chosen BS period (all customers)
    order_qs = Order.objects.all()
    if from_date or to_date:
        if from_date:
            order_qs = order_qs.filter(order_date__gte=from_date)
        if to_date:
            order_qs = order_qs.filter(order_date__lte=to_date)
    else:
        order_qs = order_qs.filter(order_date__month=month, order_date__year=year)
    customer_sales = order_qs.aggregate(total_amount=Sum("total"))
    totals["customer_amount"] = customer_sales.get("total_amount") or 0

    # For now, take stock as equal to purchases (no sales deduction yet)
    totals["gold_stock_amount"] = totals["gold_purchase_amount"]
    totals["gold_stock_weight"] = totals["gold_purchase_weight"]
    totals["silver_stock_amount"] = totals["silver_purchase_amount"]
    totals["silver_stock_weight"] = totals["silver_purchase_weight"]

    # Build month/year choices (BS) for the selector
    months = [
        {"value": m, "label": name}
        for m, name in NEPALI_MONTHS.items()
    ]
    # Simple BS year range around the currently selected year
    years = [year - 2, year - 1, year, year + 1, year + 2]

    context = {
        "totals": totals,
        "month": month,
        "year": year,
        "month_name": NEPALI_MONTHS.get(month, str(month)),
        "months": months,
        "years": years,
        "from_date": from_date_str,
        "to_date": to_date_str,
    }
    return render(request, "main/monthly_stock_report.html", context)
