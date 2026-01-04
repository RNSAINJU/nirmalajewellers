from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Q
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta
import nepali_datetime as ndt

from ornament.models import Ornament, Kaligar
from goldsilverpurchase.models import GoldSilverPurchase, Party, CustomerPurchase
from order.models import Order, OrderOrnament
from main.models import Stock

# Create your views here.

def index(request):
    return HttpResponse("Hello, Django on Ubuntu!")


def dashboard(request):
    """Dashboard with basic counts and totals across apps."""
    total_ornaments = Ornament.objects.count()
    total_orders = Order.objects.count()
    total_purchase_amount = GoldSilverPurchase.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_order_amount = Order.objects.aggregate(total=Sum('total'))['total'] or 0

    # Stock report by metal type
    # Gold stock: sum of all gold purchases (quantity)
    gold_stock = (
        GoldSilverPurchase.objects.filter(metal_type__icontains="gold")
        .aggregate(total=Sum("quantity"))
        .get("total")
        or 0
    )

    # Diamond stock: total diamond_weight of all Diamond ornaments
    diamond_stock = (
        Ornament.objects.filter(metal_type=Ornament.MetalTypeCategory.DIAMOND)
        .aggregate(total=Sum('diamond_weight'))
        .get('total')
        or 0
    )

    # Silver stock: sum of all silver purchases (quantity)
    silver_stock = (
        GoldSilverPurchase.objects.filter(metal_type__icontains="silver")
        .aggregate(total=Sum("quantity"))
        .get("total")
        or 0
    )

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


def stock_report(request):
    """Stock report filtered by optional date range (BS).

    Shows sales and purchase totals for all records, or filtered by
    from_date and to_date parameters (Bikram Sambat).
    """

    # Optional BS date range (YYYY-MM-DD)
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

    # Global totals for the selected BS month/year
    totals = {
        "gold_purchase_amount": 0,
        "silver_purchase_amount": 0,
        "diamond_purchase_amount": 0,
        "customer_amount": 0,
        "sales_amount": 0,
        "gold_purchase_weight": 0,
        "silver_purchase_weight": 0,
        "diamond_purchase_weight": 0,
        "sales_weight": 0,
        "gold_stock_amount": 0,
        "silver_stock_amount": 0,
        "diamond_stock_amount": 0,
        "gold_stock_weight": 0,
        "silver_stock_weight": 0,
        "diamond_stock_weight": 0,
    }

    # Helper: customer purchase inflow by metal (refined_weight + amount)
    def customer_purchase_totals(metal_type):
        qs = CustomerPurchase.objects.filter(metal_type__icontains=metal_type)
        if from_date:
            qs = qs.filter(purchase_date__gte=from_date)
        if to_date:
            qs = qs.filter(purchase_date__lte=to_date)
        agg = qs.aggregate(total_amount=Sum("amount"), total_weight=Sum("refined_weight"))
        return (
            agg.get("total_amount") or Decimal("0"),
            agg.get("total_weight") or Decimal("0"),
        )

    # Gold purchases (all parties) for the chosen BS period
    # Use case-insensitive containment to tolerate imported values like 'Gold', ' GOLD ', etc.
    gold_qs = GoldSilverPurchase.objects.filter(metal_type__icontains="gold")
    if from_date:
        gold_qs = gold_qs.filter(bill_date__gte=from_date)
    if to_date:
        gold_qs = gold_qs.filter(bill_date__lte=to_date)
    gold_purchases = gold_qs.aggregate(
        total_amount=Sum("amount"),
        total_wages=Sum("wages"),
        total_qty=Sum("quantity"),
    )
    gold_cust_amount, gold_cust_weight = customer_purchase_totals("gold")
    totals["gold_purchase_amount"] = (
        (gold_purchases.get("total_amount") or Decimal("0"))
        - (gold_purchases.get("total_wages") or Decimal("0"))
        + gold_cust_amount
    )
    totals["gold_purchase_weight"] = (gold_purchases.get("total_qty") or 0) + gold_cust_weight

    # Silver purchases (all parties) for the chosen BS period
    silver_qs = GoldSilverPurchase.objects.filter(metal_type__icontains="silver")
    if from_date:
        silver_qs = silver_qs.filter(bill_date__gte=from_date)
    if to_date:
        silver_qs = silver_qs.filter(bill_date__lte=to_date)
    silver_purchases = silver_qs.aggregate(
        total_amount=Sum("amount"),
        total_wages=Sum("wages"),
        total_qty=Sum("quantity"),
    )
    silver_cust_amount, silver_cust_weight = customer_purchase_totals("silver")
    totals["silver_purchase_amount"] = (
        (silver_purchases.get("total_amount") or Decimal("0"))
        - (silver_purchases.get("total_wages") or Decimal("0"))
        + silver_cust_amount
    )
    totals["silver_purchase_weight"] = (silver_purchases.get("total_qty") or 0) + silver_cust_weight

    # Diamond purchases (all parties) for the chosen BS period
    diamond_qs = GoldSilverPurchase.objects.filter(metal_type__icontains="diamond")
    if from_date:
        diamond_qs = diamond_qs.filter(bill_date__gte=from_date)
    if to_date:
        diamond_qs = diamond_qs.filter(bill_date__lte=to_date)
    diamond_purchases = diamond_qs.aggregate(total_amount=Sum("amount"), total_qty=Sum("quantity"))
    diamond_cust_amount, diamond_cust_weight = customer_purchase_totals("diamond")
    totals["diamond_purchase_amount"] = (diamond_purchases.get("total_amount") or Decimal("0")) + diamond_cust_amount
    totals["diamond_purchase_weight"] = (diamond_purchases.get("total_qty") or 0) + diamond_cust_weight

    # Wages from all purchases
    wages_qs = GoldSilverPurchase.objects.all()
    if from_date:
        wages_qs = wages_qs.filter(bill_date__gte=from_date)
    if to_date:
        wages_qs = wages_qs.filter(bill_date__lte=to_date)
    wages_agg = wages_qs.aggregate(total_wages=Sum("wages"))
    total_wages = wages_agg.get("total_wages") or 0

    # Customer sales (orders) for the chosen BS period (all customers)
    order_qs = Order.objects.all()
    if from_date:
        order_qs = order_qs.filter(order_date__gte=from_date)
    if to_date:
        order_qs = order_qs.filter(order_date__lte=to_date)
    customer_sales = order_qs.aggregate(total_amount=Sum("total"))
    totals["customer_amount"] = customer_sales.get("total_amount") or 0

    # Sales detail (line amounts) grouped by ornament metal type
    sales_qs = OrderOrnament.objects.select_related("order", "ornament")
    if from_date:
        sales_qs = sales_qs.filter(order__order_date__gte=from_date)
    if to_date:
        sales_qs = sales_qs.filter(order__order_date__lte=to_date)

    def aggregate_sales(metal_type, weight_field):
        qs = sales_qs.filter(ornament__metal_type__icontains=metal_type)
        agg = qs.aggregate(total_amount=Sum("line_amount"), total_weight=Sum(weight_field))
        return (
            agg.get("total_amount") or 0,
            agg.get("total_weight") or 0,
        )

    diamond_sales_amount, diamond_sales_weight = aggregate_sales("diamond", "ornament__diamond_weight")
    gold_sales_amount, gold_sales_weight = aggregate_sales("gold", "ornament__weight")
    silver_sales_amount, silver_sales_weight = aggregate_sales("silver", "ornament__weight")

    totals["sales_amount"] = diamond_sales_amount + gold_sales_amount + silver_sales_amount
    totals["sales_weight"] = diamond_sales_weight + gold_sales_weight + silver_sales_weight

    # Compute stock as purchases minus sales
    totals["gold_stock_amount"] = (totals["gold_purchase_amount"] or Decimal("0")) - (gold_sales_amount or Decimal("0"))
    totals["gold_stock_weight"] = (totals["gold_purchase_weight"] or Decimal("0")) - (gold_sales_weight or Decimal("0"))
    totals["silver_stock_amount"] = (totals["silver_purchase_amount"] or Decimal("0")) - (silver_sales_amount or Decimal("0"))
    totals["silver_stock_weight"] = (totals["silver_purchase_weight"] or Decimal("0")) - (silver_sales_weight or Decimal("0"))
    totals["diamond_stock_amount"] = (totals["diamond_purchase_amount"] or Decimal("0")) - (diamond_sales_amount or Decimal("0"))
    totals["diamond_stock_weight"] = (totals["diamond_purchase_weight"] or Decimal("0")) - (diamond_sales_weight or Decimal("0"))

    purchase_rows = [
        {"label": "Diamond", "qty": totals["diamond_purchase_weight"], "amount": totals["diamond_purchase_amount"]},
        {"label": "Gold", "qty": totals["gold_purchase_weight"], "amount": totals["gold_purchase_amount"]},
        {"label": "Silver", "qty": totals["silver_purchase_weight"], "amount": totals["silver_purchase_amount"]},
        {"label": "Jardi", "qty": 0, "amount": 0},
        {"label": "Wages", "qty": 0, "amount": total_wages},
    ]

    # Sales extras: Jardi and Wages from order line items
    sales_jardi_amount = sales_qs.aggregate(total_jardi=Sum("jarti")).get("total_jardi") or Decimal("0")
    sales_wages_amount = sales_qs.aggregate(total_wages=Sum("jyala")).get("total_wages") or Decimal("0")

    sales_rows = [
        {"label": "Diamond", "qty": diamond_sales_weight, "amount": diamond_sales_amount},
        {"label": "Gold", "qty": gold_sales_weight, "amount": gold_sales_amount},
        {"label": "Silver", "qty": silver_sales_weight, "amount": silver_sales_amount},
        {"label": "Jardi", "qty": 0, "amount": sales_jardi_amount},
        {"label": "Wages", "qty": 0, "amount": sales_wages_amount},
    ]

    purchase_totals = {
        "qty": sum(row["qty"] for row in purchase_rows),
        "amount": sum(row["amount"] for row in purchase_rows),
    }

    sales_totals = {
        "qty": sum(row["qty"] for row in sales_rows),
        "amount": sum(row["amount"] for row in sales_rows),
    }

    # Purchase extras: Jardi from purchase 'particular' and Wages from purchases.wages
    purchase_jardi_qs = GoldSilverPurchase.objects.filter(Q(particular__icontains="jardi") | Q(particular__icontains="jarti"))
    if 'from_date' in locals() and from_date:
        purchase_jardi_qs = purchase_jardi_qs.filter(bill_date__gte=from_date)
    if 'to_date' in locals() and to_date:
        purchase_jardi_qs = purchase_jardi_qs.filter(bill_date__lte=to_date)
    purchase_jardi_amount = purchase_jardi_qs.aggregate(total_amount=Sum("amount")).get("total_amount") or Decimal("0")

    # Fetch previous year remaining stock
    # Try to get stock for year 2082 first, if not available use any previous year
    try:
        stock_data = Stock.objects.get(year=2082)
    except Stock.DoesNotExist:
        # If 2082 not found, get the most recent stock data
        stock_data = Stock.objects.order_by('-year').first()
    
    opening_diamond = Decimal("0")
    opening_gold = Decimal("0")
    opening_silver = Decimal("0")
    opening_jardi = Decimal("0")
    opening_wages = Decimal("0")
    opening_diamond_amount = Decimal("0")
    opening_gold_amount = Decimal("0")
    opening_silver_amount = Decimal("0")
    
    opening_stock_rows = []
    opening_stock_totals = {"qty": Decimal("0"), "amount": Decimal("0")}
    
    if stock_data:
        opening_diamond = stock_data.diamond
        opening_gold = stock_data.gold
        opening_silver = stock_data.silver
        opening_jardi = stock_data.jardi
        opening_wages = stock_data.wages
        
        # Calculate amounts using rates
        opening_diamond_amount = opening_diamond * (stock_data.diamond_rate or Decimal("0"))
        opening_gold_amount = opening_gold * (stock_data.gold_rate or Decimal("0"))
        opening_silver_amount = opening_silver * (stock_data.silver_rate or Decimal("0"))
        
        opening_stock_rows = [
            {"label": "Diamond", "qty": opening_diamond, "amount": opening_diamond_amount},
            {"label": "Gold", "qty": opening_gold, "amount": opening_gold_amount},
            {"label": "Silver", "qty": opening_silver, "amount": opening_silver_amount},
            {"label": "Jardi", "qty": Decimal("0"), "amount": opening_jardi},
            {"label": "Wages", "qty": Decimal("0"), "amount": opening_wages},
        ]
        opening_stock_totals = {
            "qty": opening_diamond + opening_gold + opening_silver,
            "amount": opening_diamond_amount + opening_gold_amount + opening_silver_amount + opening_jardi + opening_wages,
        }

    # Calculate stock as: Opening + Purchase - Sales
    stock_rows = [
        {"label": "Diamond", "qty": opening_diamond + (totals["diamond_purchase_weight"] or Decimal("0")) - (diamond_sales_weight or Decimal("0")), "amount": opening_diamond_amount + (totals["diamond_purchase_amount"] or Decimal("0")) - (diamond_sales_amount or Decimal("0"))},
        {"label": "Gold", "qty": opening_gold + (totals["gold_purchase_weight"] or Decimal("0")) - (gold_sales_weight or Decimal("0")), "amount": opening_gold_amount + (totals["gold_purchase_amount"] or Decimal("0")) - (gold_sales_amount or Decimal("0"))},
        {"label": "Silver", "qty": opening_silver + (totals["silver_purchase_weight"] or Decimal("0")) - (silver_sales_weight or Decimal("0")), "amount": opening_silver_amount + (totals["silver_purchase_amount"] or Decimal("0")) - (silver_sales_amount or Decimal("0"))},
        {"label": "Jardi", "qty": Decimal("0"), "amount": opening_jardi + (purchase_jardi_amount or Decimal("0")) - (sales_jardi_amount or Decimal("0"))},
        {"label": "Wages", "qty": Decimal("0"), "amount": opening_wages + (total_wages or Decimal("0")) - (sales_wages_amount or Decimal("0"))},
    ]

    stock_totals = {
        "qty": sum(row["qty"] for row in stock_rows),
        "amount": sum(row["amount"] for row in stock_rows),
    }

    context = {
        "totals": totals,
        "purchase_rows": purchase_rows,
        "sales_rows": sales_rows,
        "purchase_totals": purchase_totals,
        "sales_totals": sales_totals,
        "stock_rows": stock_rows,
        "stock_totals": stock_totals,
        "opening_stock_rows": opening_stock_rows,
        "opening_stock_totals": opening_stock_totals,
    }
    return render(request, "main/stock_report.html", context)


def monthly_stock_report(request):
    """Monthly stock report filtered by BS month (YYYY-MM).

    Final stock per metal = (purchases + customer purchases) - sales within the month.
    """

    month_str = request.GET.get("month") or ""
    today_bs = ndt.date.today()

    try:
        y, m = map(int, month_str.split("-")) if month_str else (today_bs.year, today_bs.month)
        start_date = ndt.date(y, m, 1)
        # Compute last day of month
        if m == 12:
            end_date = ndt.date(y + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = ndt.date(y, m + 1, 1) - timedelta(days=1)
    except Exception:
        start_date = ndt.date(today_bs.year, today_bs.month, 1)
        end_date = (ndt.date(today_bs.year + 1, 1, 1) - timedelta(days=1)) if today_bs.month == 12 else (ndt.date(today_bs.year, today_bs.month + 1, 1) - timedelta(days=1))
        month_str = f"{start_date.year:04d}-{start_date.month:02d}"

    def gs_purchase_totals(metal_type: str):
        qs = GoldSilverPurchase.objects.filter(
            metal_type__icontains=metal_type,
            bill_date__gte=start_date,
            bill_date__lte=end_date,
        )
        agg = qs.aggregate(total_amount=Sum("amount"), total_wages=Sum("wages"), total_qty=Sum("quantity"))
        net_amount = (agg.get("total_amount") or Decimal("0")) - (agg.get("total_wages") or Decimal("0"))
        return net_amount, (agg.get("total_qty") or Decimal("0"))

    def customer_purchase_totals(metal_type: str):
        qs = CustomerPurchase.objects.filter(
            metal_type__icontains=metal_type,
            purchase_date__gte=start_date,
            purchase_date__lte=end_date,
        )
        agg = qs.aggregate(total_amount=Sum("amount"), total_weight=Sum("refined_weight"))
        return (agg.get("total_amount") or Decimal("0")), (agg.get("total_weight") or Decimal("0"))

    def sales_totals(metal_type: str, weight_field: str):
        qs = OrderOrnament.objects.select_related("order", "ornament").filter(
            order__order_date__gte=start_date,
            order__order_date__lte=end_date,
            ornament__metal_type__icontains=metal_type,
        )
        agg = qs.aggregate(total_amount=Sum("line_amount"), total_weight=Sum(weight_field))
        return (agg.get("total_amount") or Decimal("0")), (agg.get("total_weight") or Decimal("0"))

    metals = [
        ("gold", "Gold", "weight"),
        ("silver", "Silver", "weight"),
        ("diamond", "Diamond", "diamond_weight"),
    ]

    purchase_rows = []
    sales_rows = []
    stock_rows = []
    metal_summary = []

    for key, label, sales_weight_field in metals:
        gs_amount, gs_qty = gs_purchase_totals(key)
        cust_amount, cust_qty = customer_purchase_totals(key)
        metal_purchase_amount = gs_amount + cust_amount
        metal_purchase_qty = gs_qty + cust_qty

        sales_amount, sales_qty = sales_totals(key, f"ornament__{sales_weight_field}")

        purchase_rows.append({"label": label, "qty": metal_purchase_qty, "amount": metal_purchase_amount})
        sales_rows.append({"label": label, "qty": sales_qty, "amount": sales_amount})

        stock_rows.append({
            "label": label,
            "qty": metal_purchase_qty - sales_qty,
            "amount": metal_purchase_amount - sales_amount,
        })

        metal_summary.append({
            "label": label,
            "purchase_qty": metal_purchase_qty,
            "purchase_amount": metal_purchase_amount,
            "sales_qty": sales_qty,
            "sales_amount": sales_amount,
            "stock_qty": metal_purchase_qty - sales_qty,
            "stock_amount": metal_purchase_amount - sales_amount,
        })

    purchase_totals = {
        "qty": sum(row["qty"] for row in purchase_rows),
        "amount": sum(row["amount"] for row in purchase_rows),
    }

    sales_totals_dict = {
        "qty": sum(row["qty"] for row in sales_rows),
        "amount": sum(row["amount"] for row in sales_rows),
    }

    stock_totals = {
        "qty": sum(row["qty"] for row in stock_rows),
        "amount": sum(row["amount"] for row in stock_rows),
    }

    context = {
        "month": month_str or f"{start_date.year:04d}-{start_date.month:02d}",
        "purchase_rows": purchase_rows,
        "sales_rows": sales_rows,
        "stock_rows": stock_rows,
        "metal_summary": metal_summary,
        "purchase_totals": purchase_totals,
        "sales_totals": sales_totals_dict,
        "stock_totals": stock_totals,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "main/monthly_stock_report.html", context)


def add_stock(request):
    """View to add stock details manually."""
    from django.shortcuts import redirect
    from .forms import StockForm
    
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, f'Stock for year {form.cleaned_data["year"]} added successfully!')
            return redirect('ornament:rates_and_stock')
    else:
        form = StockForm()
    
    context = {
        'form': form,
        'page_title': 'Add Stock Details',
    }
    return render(request, 'main/stock_form.html', context)


def edit_stock(request, year):
    """View to edit stock details for a specific year."""
    from django.shortcuts import redirect, get_object_or_404
    from .forms import StockForm
    
    stock = get_object_or_404(Stock, year=year)
    
    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, f'Stock for year {form.cleaned_data["year"]} updated successfully!')
            return redirect('ornament:rates_and_stock')
    else:
        form = StockForm(instance=stock)
    
    context = {
        'form': form,
        'stock': stock,
        'page_title': f'Edit Stock Details - Year {year}',
    }
    return render(request, 'main/stock_form.html', context)
