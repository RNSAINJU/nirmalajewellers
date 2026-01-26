from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Q, F, DecimalField
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta, date
import nepali_datetime as ndt
from django.contrib import messages

from ornament.models import Ornament, Kaligar
from goldsilverpurchase.models import GoldSilverPurchase, Party, CustomerPurchase
from order.models import Order, OrderOrnament
from main.models import Stock, DailyRate
from main.forms import DailyRateForm

# Create your views here.

def calculate_daily_ornament_totals(target_date, gold_rate=None, silver_rate=None, diamond_rate=None, use_date_filter=False):
    """
    Calculate total ornament values for a given date.
    
    Args:
        target_date: The date for getting rates
        gold_rate: Override gold rate (optional, assumed to be per tola)
        silver_rate: Override silver rate (optional, assumed to be per tola)
        diamond_rate: Override diamond rate (optional, per gram)
        use_date_filter: If True, filter ornaments by created_at__date=target_date
                        If False, use all current stock ornaments
    
    Note: Gold/Silver daily rates are in per-tola basis (1 tola = 11.66 grams)
    Returns dict with metal totals based on weight report logic.
    """
    from datetime import datetime as dt
    
    # Conversion factor: 1 tola = 11.66 grams
    TOLA_TO_GRAMS = Decimal('11.66')
    
    result = {
        'date': target_date,
        'gold_amount': Decimal('0'),
        'silver_amount': Decimal('0'),
        'diamond_amount': Decimal('0'),
        'gold_count': 0,
        'silver_count': 0,
        'diamond_count': 0,
        'gold_weight': Decimal('0'),
        'silver_weight': Decimal('0'),
        'diamond_weight': Decimal('0'),
        'total_amount': Decimal('0'),
    }
    
    # Try to get rates for the target date
    if gold_rate is None or silver_rate is None or diamond_rate is None:
        try:
            rate_obj = DailyRate.objects.order_by('-created_at').first()
            if rate_obj:
                if gold_rate is None:
                    gold_rate = rate_obj.gold_rate
                if silver_rate is None:
                    silver_rate = rate_obj.silver_rate
                if diamond_rate is None:
                    diamond_rate = rate_obj.diamond_rate
            else:
                if gold_rate is None:
                    gold_rate = Decimal('0')
                if silver_rate is None:
                    silver_rate = Decimal('0')
                if diamond_rate is None:
                    diamond_rate = Decimal('0')
        except:
            if gold_rate is None:
                gold_rate = Decimal('0')
            if silver_rate is None:
                silver_rate = Decimal('0')
            if diamond_rate is None:
                diamond_rate = Decimal('0')
    
    # Convert tola rates to per-gram rates for gold and silver
    gold_rate_per_gram = gold_rate / TOLA_TO_GRAMS if gold_rate > 0 else Decimal('0')
    silver_rate_per_gram = silver_rate / TOLA_TO_GRAMS if silver_rate > 0 else Decimal('0')
    
    # Filter ornaments: all current stock or filtered by date
    if use_date_filter:
        ornaments_today = Ornament.objects.filter(
            ornament_type=Ornament.OrnamentCategory.STOCK,
            created_at__date=target_date
        )
    else:
        # Use all current stock ornaments (regardless of created_at date)
        ornaments_today = Ornament.objects.filter(
            ornament_type=Ornament.OrnamentCategory.STOCK
        )
    
    # Purity conversion factors for 24k equivalent
    purity_factors = {
        '24KARAT': Decimal('1.00'),
        '23KARAT': Decimal('0.99'),
        '22KARAT': Decimal('0.98'),
        '18KARAT': Decimal('0.75'),
        '14KARAT': Decimal('0.58'),
    }
    
    # Process Gold ornaments
    gold_ornaments = ornaments_today.filter(metal_type='Gold')
    if gold_ornaments.exists():
        result['gold_count'] = gold_ornaments.count()
        
        # Calculate 24k equivalent by iterating through ornaments
        gold_24k_equivalent = Decimal('0')
        total_gold_weight = Decimal('0')
        for ornament in gold_ornaments:
            weight = ornament.weight or Decimal('0')
            total_gold_weight += weight
            factor = purity_factors.get(ornament.type, Decimal('1.00'))
            gold_24k_equivalent += weight * factor
        
        result['gold_weight'] = total_gold_weight
        
        # Calculate jarti and jyala amounts
        total_jarti = gold_ornaments.aggregate(total=Sum('jarti'))['total'] or Decimal('0')
        total_jyala = gold_ornaments.aggregate(total=Sum('jyala'))['total'] or Decimal('0')
        
        # Calculate amounts with per-gram rate
        if gold_rate_per_gram and gold_rate_per_gram > 0:
            gold_amount = gold_24k_equivalent * gold_rate_per_gram
            jarti_amount = total_jarti * gold_rate_per_gram
            result['gold_amount'] = gold_amount + jarti_amount + total_jyala
    
    # Process Silver ornaments
    silver_ornaments = ornaments_today.filter(metal_type='Silver')
    if silver_ornaments.exists():
        result['silver_count'] = silver_ornaments.count()
        
        # Calculate 24k equivalent for silver
        silver_24k_equivalent = Decimal('0')
        total_silver_weight = Decimal('0')
        for ornament in silver_ornaments:
            weight = ornament.weight or Decimal('0')
            total_silver_weight += weight
            factor = purity_factors.get(ornament.type, Decimal('1.00'))
            silver_24k_equivalent += weight * factor
        
        result['silver_weight'] = total_silver_weight
        
        # Calculate amounts with per-gram rate
        if silver_rate_per_gram and silver_rate_per_gram > 0:
            silver_amount = silver_24k_equivalent * silver_rate_per_gram
            total_jyala = silver_ornaments.aggregate(total=Sum('jyala'))['total'] or Decimal('0')
            result['silver_amount'] = silver_amount + total_jyala
    
    # Process Diamond ornaments
    diamond_ornaments = ornaments_today.filter(metal_type='Diamond')
    if diamond_ornaments.exists():
        result['diamond_count'] = diamond_ornaments.count()
        
        # For diamond ornaments, calculate four components:
        # 1. Metal weight (24K equivalent) valued at gold rate
        # 2. Diamond weight valued at diamond rate
        # 3. Jyala amounts
        # 4. Stone price amounts
        
        # Component 1: Calculate 24K equivalent metal weight
        diamond_24k_equivalent = Decimal('0')
        diamond_metal_weight_for_display = Decimal('0')
        
        for ornament in diamond_ornaments:
            weight = ornament.weight or Decimal('0')
            factor = purity_factors.get(ornament.type, Decimal('1.00'))
            diamond_24k_equivalent += weight * factor
            diamond_metal_weight_for_display = diamond_24k_equivalent
        
        result['diamond_weight'] = diamond_metal_weight_for_display
        
        # Component 1 value: Convert to tola and multiply by gold rate
        TOLA_CONVERSION = Decimal('11.664')
        diamond_metal_weight_in_tola = diamond_24k_equivalent / TOLA_CONVERSION
        component1_amount = diamond_metal_weight_in_tola * gold_rate if gold_rate > 0 else Decimal('0')
        
        # Component 2: Sum all diamond_weight and multiply by stock diamond_rate
        total_actual_diamond_weight = diamond_ornaments.aggregate(total=Sum('diamond_weight'))['total'] or Decimal('0')
        
        # Get stock data for diamond_rate
        # First try current year, then fall back to most recent stock record
        stock_record = Stock.objects.filter(year=target_date.year).first()
        if not stock_record:
            # If no record for current year, get the most recent one
            stock_record = Stock.objects.order_by('-year').first()
        
        if stock_record and stock_record.diamond_rate:
            diamond_rate_to_use = stock_record.diamond_rate
            # diamond_weight is in carat, diamond_rate is per carat (no conversion needed)
            component2_amount = total_actual_diamond_weight * diamond_rate_to_use
        else:
            component2_amount = Decimal('0')
        
        # Component 3: Sum all jyala amounts
        component3_amount = diamond_ornaments.aggregate(total=Sum('jyala'))['total'] or Decimal('0')
        
        # Component 4: Sum all stone_price amounts
        component4_amount = diamond_ornaments.aggregate(total=Sum('stone_totalprice'))['total'] or Decimal('0')
        
        # Total diamond amount = all components
        diamond_amount = component1_amount + component2_amount + component3_amount + component4_amount
        result['diamond_amount'] = diamond_amount
    
    result['total_amount'] = result['gold_amount'] + result['silver_amount'] + result['diamond_amount']
    
    return result


def index(request):
    """Home page."""
    return HttpResponse("Hello, Django on Ubuntu!")


def dashboard(request):
    """Dashboard with basic counts and totals across apps."""
    daily_rate_form = None
    
    # Handle POST request to update today's rates
    if request.method == 'POST':
        daily_rate_form = DailyRateForm(request.POST)
        if daily_rate_form.is_valid():
            # Get or create today's rate using bs_date
            bs_date = daily_rate_form.cleaned_data.get('bs_date')
            daily_rate, created = DailyRate.objects.get_or_create(bs_date=bs_date)
            
            # Update rates
            daily_rate.gold_rate = daily_rate_form.cleaned_data['gold_rate']
            daily_rate.silver_rate = daily_rate_form.cleaned_data['silver_rate']
            # Auto-calculate per-10g rates from per-tola inputs: (tola_rate / 11.664) * 10
            tola_to_10g = Decimal('10') / Decimal('11.664')
            daily_rate.gold_rate_10g = (daily_rate.gold_rate or Decimal('0')) * tola_to_10g
            daily_rate.silver_rate_10g = (daily_rate.silver_rate or Decimal('0')) * tola_to_10g
            daily_rate.save()
            
            action = 'created' if created else 'updated'
            messages.success(request, f'Today\'s rates {action} successfully!')
            return redirect('main:dashboard')
    else:
        # Get most recent rate
        today_rate = DailyRate.objects.order_by('-created_at').first()
        if today_rate:
            daily_rate_form = DailyRateForm(instance=today_rate)
        else:
            daily_rate_form = DailyRateForm()
    
    total_ornaments = Ornament.objects.count()
    total_orders = Order.objects.count()
    total_purchase_amount = GoldSilverPurchase.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_order_amount = Order.objects.aggregate(total=Sum('total'))['total'] or 0

    # Sales by month for chart
    from django.db.models.functions import TruncMonth
    sales_by_month_qs = (
        Order.objects
        .filter(order_date__isnull=False)
        .annotate(month=TruncMonth('order_date'))
        .values('month')
        .annotate(total=Sum('total'))
        .order_by('month')
    )
    import json
    sales_month_labels = [x['month'].strftime('%b %Y') if x['month'] else '' for x in sales_by_month_qs]
    sales_month_totals = [float(x['total'] or 0) for x in sales_by_month_qs]
    # For Chart.js, serialize as JSON for safe JS rendering
    sales_month_labels_json = json.dumps(sales_month_labels)
    sales_month_totals_json = json.dumps(sales_month_totals)

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
    
    # Calculate daily P&L using bs_date from DailyRate
    # Get today's and yesterday's rates from DailyRate table
    today_rate = DailyRate.objects.order_by('-created_at').first()
    yesterday_rate = DailyRate.objects.order_by('-created_at')[1:2].first()
    
    today_date_label = today_rate.bs_date if today_rate else "Today"
    yesterday_date_label = yesterday_rate.bs_date if yesterday_rate else "Yesterday"
    
    # Calculate totals using today's and yesterday's rates
    if today_rate:
        today_totals = calculate_daily_ornament_totals(
            date.today(),
            gold_rate=today_rate.gold_rate,
            silver_rate=today_rate.silver_rate,
            diamond_rate=Decimal('0'),
            use_date_filter=False
        )
    else:
        today_totals = calculate_daily_ornament_totals(date.today(), use_date_filter=False)
    
    if yesterday_rate:
        yesterday_totals = calculate_daily_ornament_totals(
            date.today(),
            gold_rate=yesterday_rate.gold_rate,
            silver_rate=yesterday_rate.silver_rate,
            diamond_rate=Decimal('0'),
            use_date_filter=False
        )
    else:
        yesterday_totals = calculate_daily_ornament_totals(date.today(), use_date_filter=False)
    
    # Calculate stock closing rate totals (using stock year rates instead of daily rates)
    current_year = date.today().year
    stock_data = Stock.objects.filter(year=current_year).first()
    if not stock_data:
        # Fall back to most recent stock record if current year not available
        stock_data = Stock.objects.order_by('-year').first()
    
    if stock_data:
        stock_closing_totals = calculate_daily_ornament_totals(
            date.today(),
            gold_rate=stock_data.gold_rate,
            silver_rate=stock_data.silver_rate,
            diamond_rate=stock_data.diamond_rate,
            use_date_filter=False
        )
    else:
        stock_closing_totals = calculate_daily_ornament_totals(date.today(), use_date_filter=False)
    
    # Calculate differences
    pl_difference = today_totals['total_amount'] - yesterday_totals['total_amount']
    pl_percent_change = Decimal('0')
    if yesterday_totals['total_amount'] > 0:
        pl_percent_change = (pl_difference / yesterday_totals['total_amount']) * Decimal('100')
    
    # Calculate individual metal differences (today vs yesterday)
    pl_gold_diff = today_totals['gold_amount'] - yesterday_totals['gold_amount']
    pl_silver_diff = today_totals['silver_amount'] - yesterday_totals['silver_amount']
    pl_diamond_diff = today_totals['diamond_amount'] - yesterday_totals['diamond_amount']
    
    # Calculate percentage changes for individual metals (today vs yesterday)
    pl_gold_percent = Decimal('0')
    if yesterday_totals['gold_amount'] > 0:
        pl_gold_percent = (pl_gold_diff / yesterday_totals['gold_amount']) * Decimal('100')
    
    pl_silver_percent = Decimal('0')
    if yesterday_totals['silver_amount'] > 0:
        pl_silver_percent = (pl_silver_diff / yesterday_totals['silver_amount']) * Decimal('100')
    
    pl_diamond_percent = Decimal('0')
    if yesterday_totals['diamond_amount'] > 0:
        pl_diamond_percent = (pl_diamond_diff / yesterday_totals['diamond_amount']) * Decimal('100')
    
    # Calculate closing vs today differences (today's rate - closing rate)
    closing_today_difference = today_totals['total_amount'] - stock_closing_totals['total_amount']
    closing_today_gold_diff = today_totals['gold_amount'] - stock_closing_totals['gold_amount']
    closing_today_silver_diff = today_totals['silver_amount'] - stock_closing_totals['silver_amount']
    closing_today_diamond_diff = today_totals['diamond_amount'] - stock_closing_totals['diamond_amount']
    
    # Calculate percentage changes for closing vs today
    closing_today_percent = Decimal('0')
    if stock_closing_totals['total_amount'] > 0:
        closing_today_percent = (closing_today_difference / stock_closing_totals['total_amount']) * Decimal('100')
    
    closing_today_gold_percent = Decimal('0')
    if stock_closing_totals['gold_amount'] > 0:
        closing_today_gold_percent = (closing_today_gold_diff / stock_closing_totals['gold_amount']) * Decimal('100')
    
    closing_today_silver_percent = Decimal('0')
    if stock_closing_totals['silver_amount'] > 0:
        closing_today_silver_percent = (closing_today_silver_diff / stock_closing_totals['silver_amount']) * Decimal('100')
    
    closing_today_diamond_percent = Decimal('0')
    if stock_closing_totals['diamond_amount'] > 0:
        closing_today_diamond_percent = (closing_today_diamond_diff / stock_closing_totals['diamond_amount']) * Decimal('100')
    
    # Get most recent rate for display
    latest_rate = today_rate

    context = {
        'total_ornaments': total_ornaments,
        'total_orders': total_orders,
        'total_purchase_amount': total_purchase_amount,
        'total_order_amount': total_order_amount,
        'gold_stock': gold_stock,
        'silver_stock': silver_stock,
        'diamond_stock': diamond_stock,
        'daily_rate_form': daily_rate_form,
        'latest_rate': latest_rate,
        'today_totals': today_totals,
        'yesterday_totals': yesterday_totals,
        'stock_closing_totals': stock_closing_totals,
        'pl_difference': pl_difference,
        'pl_percent_change': pl_percent_change,
        'pl_gold_diff': pl_gold_diff,
        'pl_silver_diff': pl_silver_diff,
        'pl_diamond_diff': pl_diamond_diff,
        'pl_gold_percent': pl_gold_percent,
        'pl_silver_percent': pl_silver_percent,
        'pl_diamond_percent': pl_diamond_percent,
        'closing_today_difference': closing_today_difference,
        'closing_today_percent': closing_today_percent,
        'closing_today_gold_diff': closing_today_gold_diff,
        'closing_today_silver_diff': closing_today_silver_diff,
        'closing_today_diamond_diff': closing_today_diamond_diff,
        'closing_today_gold_percent': closing_today_gold_percent,
        'closing_today_silver_percent': closing_today_silver_percent,
        'closing_today_diamond_percent': closing_today_diamond_percent,
        'today_date_label': today_date_label,
        'yesterday_date_label': yesterday_date_label,
        'today_rate': today_rate,
        'yesterday_rate': yesterday_rate,
        'sales_month_labels': sales_month_labels_json,
        'sales_month_totals': sales_month_totals_json,
    }
    return render(request, 'main/dashboard.html', context)


def daily_rates(request):
    """List and allow editing of fetched daily rates."""
    rates = DailyRate.objects.all().order_by('-created_at')

    if request.method == 'POST':
        rate_id = request.POST.get('rate_id')
        gold_rate_raw = request.POST.get('gold_rate')
        silver_rate_raw = request.POST.get('silver_rate')

        if rate_id and gold_rate_raw and silver_rate_raw:
            try:
                rate = DailyRate.objects.get(id=rate_id)
                rate.gold_rate = Decimal(gold_rate_raw)
                rate.silver_rate = Decimal(silver_rate_raw)

                # Auto-calculate per-10g rates from per-tola inputs: (tola_rate / 11.664) * 10
                tola_to_10g = Decimal('10') / Decimal('11.664')
                rate.gold_rate_10g = (rate.gold_rate or Decimal('0')) * tola_to_10g
                rate.silver_rate_10g = (rate.silver_rate or Decimal('0')) * tola_to_10g

                rate.save()
                messages.success(request, 'Rates updated successfully.')
            except DailyRate.DoesNotExist:
                messages.error(request, 'Selected rate not found.')
            except Exception:
                messages.error(request, 'Could not update rates. Please check the values and try again.')

        return redirect('main:daily_rates')

    context = {
        'rates': rates,
    }
    return render(request, 'main/daily_rates.html', context)


def add_daily_rate(request):
    """Add a new daily rate."""
    if request.method == 'POST':
        form = DailyRateForm(request.POST)
        if form.is_valid():
            rate_obj = form.save()
            
            # Auto-calculate per-10g rates from per-tola inputs
            tola_to_10g = Decimal('10') / Decimal('11.664')
            rate_obj.gold_rate_10g = (rate_obj.gold_rate or Decimal('0')) * tola_to_10g
            rate_obj.silver_rate_10g = (rate_obj.silver_rate or Decimal('0')) * tola_to_10g
            rate_obj.save()
            
            messages.success(request, 'Rate added successfully.')
            return redirect('main:daily_rates')
    else:
        form = DailyRateForm()
    
    context = {
        'form': form,
        'title': 'Add New Rate',
        'is_edit': False,
    }
    return render(request, 'main/daily_rate_form.html', context)


def edit_daily_rate(request, pk):
    """Edit a daily rate."""
    rate = get_object_or_404(DailyRate, pk=pk)
    
    if request.method == 'POST':
        form = DailyRateForm(request.POST, instance=rate)
        if form.is_valid():
            rate_obj = form.save()
            
            # Auto-calculate per-10g rates from per-tola inputs
            tola_to_10g = Decimal('10') / Decimal('11.664')
            rate_obj.gold_rate_10g = (rate_obj.gold_rate or Decimal('0')) * tola_to_10g
            rate_obj.silver_rate_10g = (rate_obj.silver_rate or Decimal('0')) * tola_to_10g
            rate_obj.save()
            
            messages.success(request, 'Rate updated successfully.')
            return redirect('main:daily_rates')
    else:
        form = DailyRateForm(instance=rate)
    
    context = {
        'form': form,
        'title': f'Edit Rate - {rate.bs_date}',
        'is_edit': True,
    }
    return render(request, 'main/daily_rate_form.html', context)


def delete_daily_rate(request, pk):
    """Delete a daily rate."""
    rate = get_object_or_404(DailyRate, pk=pk)
    
    if request.method == 'POST':
        bs_date = rate.bs_date
        rate.delete()
        messages.success(request, f'Rate for {bs_date} deleted successfully.')
        return redirect('main:daily_rates')
    
    context = {
        'object': rate,
        'object_name': 'Daily Rate',
    }
    return render(request, 'main/daily_rate_confirm_delete.html', context)



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

    # Check if a category is selected for detail view
    selected_category = request.GET.get("category")
    category_ornaments = None

    if selected_category:
        # Map display label to metal_type value
        category_map = {
            "Gold": "Gold",
            "Silver": "Silver",
            "Diamond": "Diamond",
        }
        metal_type = category_map.get(selected_category)
        if metal_type:
            from ornament.models import Ornament
            category_ornaments = Ornament.objects.filter(
                metal_type=metal_type
            ).exclude(
                ornament_type=Ornament.OrnamentCategory.SALES
            )

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
        "category_ornaments": category_ornaments,
        "selected_category": selected_category,
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
