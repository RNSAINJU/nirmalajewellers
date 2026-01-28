from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, DecimalField, Q
from django.db.models.functions import Coalesce
from decimal import Decimal

from ornament.models import Ornament, Stone, Motimala, Potey
from goldsilverpurchase.models import MetalStock
from order.models import Order, OrderOrnament, OrderMetalStock
from sales.models import Sale
from main.models import DailyRate, Stock
from finance.models import SundryDebtor, CashBank


@login_required
def total_assets(request):
    """
    Calculate and display total assets including:
    - Metals from ornament weight report (Gold, Silver, Diamond)
    - Raw metals from metal stock
    - Stones, Motimala, Potey inventory
    - Order receivables
    """
    
    # Get latest rates
    latest_rate = DailyRate.objects.latest('created_at') if DailyRate.objects.exists() else None
    fallback_rate = Stock.objects.latest('year') if Stock.objects.exists() else None
    
    gold_rate = Decimal('0')
    silver_rate = Decimal('0')
    diamond_rate = Decimal('0')
    
    if latest_rate:
        gold_rate = latest_rate.gold_rate or Decimal('0')
        silver_rate = latest_rate.silver_rate or Decimal('0')
    elif fallback_rate:
        gold_rate = fallback_rate.gold_rate or Decimal('0')
        silver_rate = fallback_rate.silver_rate or Decimal('0')
        diamond_rate = fallback_rate.diamond_rate or Decimal('0')
    
    # ============================================================
    # 1. ORNAMENT INVENTORY (from weight report)
    # ============================================================
    ornaments = Ornament.objects.filter(
        ornament_type=Ornament.OrnamentCategory.STOCK,
        status=Ornament.StatusCategory.ACTIVE,
        weight__gt=0
    )
    
    # Karat conversion factors
    KARAT_FACTORS = {
        '24KARAT': Decimal('1.00'),
        '22KARAT': Decimal('0.92'),
        '18KARAT': Decimal('0.75'),
        '14KARAT': Decimal('0.58'),
    }
    
    # Gold ornaments calculation
    gold_qs = ornaments.filter(metal_type='Gold')
    gold_karats = gold_qs.values('type').annotate(weight_sum=Sum('weight'))
    gold_karat_dict = {k['type']: k['weight_sum'] or Decimal('0') for k in gold_karats}
    
    gold_24k = gold_karat_dict.get('24KARAT', Decimal('0'))
    gold_22k = gold_karat_dict.get('22KARAT', Decimal('0'))
    gold_18k = gold_karat_dict.get('18KARAT', Decimal('0'))
    gold_14k = gold_karat_dict.get('14KARAT', Decimal('0'))
    
    total_gold_weight = gold_24k + gold_22k + gold_18k + gold_14k
    gold_24k_equivalent = (gold_24k * KARAT_FACTORS['24KARAT'] + 
                          gold_22k * KARAT_FACTORS['22KARAT'] + 
                          gold_18k * KARAT_FACTORS['18KARAT'] + 
                          gold_14k * KARAT_FACTORS['14KARAT'])
    
    total_gold_amount = (gold_24k_equivalent / Decimal('11.664')) * gold_rate
    total_gold_jarti = gold_qs.aggregate(total=Sum('jarti'))['total'] or Decimal('0')
    total_gold_jyala = gold_qs.aggregate(total=Sum('jyala'))['total'] or Decimal('0')
    gold_jarti_amount = (total_gold_jarti / Decimal('11.664')) * gold_rate
    
    # Silver ornaments calculation
    silver_qs = ornaments.filter(metal_type='Silver')
    silver_karats = silver_qs.values('type').annotate(weight_sum=Sum('weight'))
    silver_karat_dict = {k['type']: k['weight_sum'] or Decimal('0') for k in silver_karats}
    
    silver_24k = silver_karat_dict.get('24KARAT', Decimal('0'))
    silver_22k = silver_karat_dict.get('22KARAT', Decimal('0'))
    silver_18k = silver_karat_dict.get('18KARAT', Decimal('0'))
    silver_14k = silver_karat_dict.get('14KARAT', Decimal('0'))
    
    total_silver_weight = silver_24k + silver_22k + silver_18k + silver_14k
    silver_24k_equivalent = (silver_24k * KARAT_FACTORS['24KARAT'] + 
                            silver_22k * KARAT_FACTORS['22KARAT'] + 
                            silver_18k * KARAT_FACTORS['18KARAT'] + 
                            silver_14k * KARAT_FACTORS['14KARAT'])
    
    total_silver_amount = (silver_24k_equivalent / Decimal('11.664')) * silver_rate
    
    # Diamond ornaments calculation (gold content in diamond ornaments)
    diamond_qs = ornaments.filter(metal_type='Diamond')
    total_diamond_weight = diamond_qs.aggregate(total=Sum('weight'))['total'] or Decimal('0')
    diamond_24k_equivalent = total_diamond_weight * Decimal('0.59')
    diamond_gold_amount = (diamond_24k_equivalent / Decimal('11.664')) * gold_rate
    
    # Diamond weight amount (diamond stones in diamond ornaments)
    diamond_weight_total = diamond_qs.aggregate(dw=Sum('diamond_weight'))['dw'] or Decimal('0')
    total_diamond_amount = diamond_weight_total * Decimal('35000')
    
    # Diamond jyala
    diamond_jyala_amount = total_diamond_weight * Decimal('1800')
    
    # Total diamond value (gold content + diamond stones + jyala)
    total_diamond_value = diamond_gold_amount + total_diamond_amount + diamond_jyala_amount
    
    # Combined totals
    ornaments_total = total_gold_amount + gold_jarti_amount + total_gold_jyala + total_silver_amount + total_diamond_value
    ornament_count = ornaments.count()
    
    # ============================================================
    # 2. RAW METALS (Bulk gold/silver not in ornaments)
    # ============================================================
    raw_gold_total = Decimal('0')
    raw_silver_total = Decimal('0')
    raw_gold_weight_total = Decimal('0')
    raw_silver_weight_total = Decimal('0')
    
    metal_stocks = MetalStock.objects.all()
    for stock in metal_stocks:
        if stock.metal_type.lower() == 'gold':
            gold_qty = stock.quantity or Decimal('0')
            raw_gold_weight_total += gold_qty
            raw_gold_total += (gold_qty / Decimal('11.664')) * gold_rate
        elif stock.metal_type.lower() == 'silver':
            silver_qty = stock.quantity or Decimal('0')
            raw_silver_weight_total += silver_qty
            raw_silver_total += (silver_qty / Decimal('11.664')) * silver_rate
    
    # ============================================================
    # CALCULATE: Raw metals used in pending orders (order, processing, completed)
    # ============================================================
    # CALCULATE: Ornament metal content in pending orders (order, processing)
    # ============================================================
    
    # Get all orders with status: order, processing (NOT completed or delivered)
    pending_orders_for_metals = Order.objects.filter(
        status__in=['order', 'processing']
    )
    
    order_gold_weight_24k = Decimal('0')
    order_silver_weight_24k = Decimal('0')
    order_gold_value = Decimal('0')
    order_silver_value = Decimal('0')
    
    # Calculate metal weights from ornaments in orders
    # Using OrderOrnament to get actual ornament weights in orders
    
    for order in pending_orders_for_metals:
        # Get all ornaments in this order
        order_ornaments = order.order_ornaments.all()
        for order_ornament in order_ornaments:
            ornament = order_ornament.ornament
            if not ornament:
                continue
            
            # Get gold weight from ornament (stored as tolas, convert using 1 tola = 11.664 gm)
            gold_weight = ornament.weight or Decimal('0')
            if gold_weight > 0 and ornament.metal_type == 'Gold':
                # Convert to 24K equivalent based on type/karat
                # ornament.type stores values like '24KARAT', '22KARAT', etc.
                ornament_type = str(ornament.type).replace('KARAT', '').replace('karat', '')
                karat_factors = {
                    '24': Decimal('1.00'),
                    '23': Decimal('0.96'),
                    '22': Decimal('0.92'),
                    '18': Decimal('0.75'),
                    '14': Decimal('0.58'),
                }
                karat_factor = karat_factors.get(ornament_type, Decimal('1.00'))
                weight_24k = gold_weight * karat_factor
                order_gold_weight_24k += weight_24k
                order_gold_value += (weight_24k / Decimal('11.664')) * gold_rate
            
            # Get silver weight from ornament
            silver_weight = ornament.weight or Decimal('0')
            if silver_weight > 0 and ornament.metal_type == 'Silver':
                # Convert to 24K equivalent based on type/karat
                ornament_type = str(ornament.type).replace('KARAT', '').replace('karat', '')
                karat_factors = {
                    '24': Decimal('1.00'),
                    '23': Decimal('0.96'),
                    '22': Decimal('0.92'),
                    '18': Decimal('0.75'),
                    '14': Decimal('0.58'),
                }
                karat_factor = karat_factors.get(ornament_type, Decimal('1.00'))
                weight_24k = silver_weight * karat_factor
                order_silver_weight_24k += weight_24k
                order_silver_value += (weight_24k / Decimal('11.664')) * silver_rate
    
    # Calculate available (final) raw metals
    raw_gold_weight_available = raw_gold_weight_total - order_gold_weight_24k
    raw_silver_weight_available = raw_silver_weight_total - order_silver_weight_24k
    raw_gold_value_available = raw_gold_total - order_gold_value
    raw_silver_value_available = raw_silver_total - order_silver_value
    
    # Use available values for total assets calculation
    raw_gold = raw_gold_value_available
    raw_silver = raw_silver_value_available
    raw_gold_weight = raw_gold_weight_available
    raw_silver_weight = raw_silver_weight_available
    
    # ============================================================
    # 3. STONES VALUE
    # ============================================================
    stones_data = Stone.objects.aggregate(total_cost=Coalesce(Sum('cost_price'), Decimal('0')))
    stones_total = stones_data['total_cost'] or Decimal('0')
    
    # ============================================================
    # 4. MOTIMALA VALUE
    # ============================================================
    motimala_data = Motimala.objects.aggregate(total_cost=Coalesce(Sum('cost_price'), Decimal('0')))
    motimala_total = motimala_data['total_cost'] or Decimal('0')
    
    # ============================================================
    # 5. POTEY VALUE
    # ============================================================
    potey_data = Potey.objects.aggregate(total_cost=Coalesce(Sum('cost_price'), Decimal('0')))
    potey_total = potey_data['total_cost'] or Decimal('0')
    
    # ============================================================
    # 6. ORDER RECEIVABLES (Amount customers owe - Remaining balance)
    # ============================================================
    # Get all orders with status: order, processing, completed (NOT delivered)
    # Sum the remaining_amount for each order
    pending_orders = Order.objects.filter(
        status__in=['order', 'processing', 'completed']
    ).aggregate(
        total=Coalesce(Sum('remaining_amount'), Decimal('0'))
    )
    order_receivable = pending_orders['total'] or Decimal('0')
    
    # ============================================================
    # 7. SUNDRY DEBTORS (Parties that owe money)
    # ============================================================
    # Get all active sundry debtors with unpaid balances
    sundry_debtors = SundryDebtor.objects.filter(is_active=True, is_paid=False)
    sundry_debtor_total = Decimal('0')
    for debtor in sundry_debtors:
        sundry_debtor_total += debtor.get_calculated_balance()
    
    # ============================================================
    # 8. CASH AND BANK BALANCES (Liquid assets)
    # ============================================================
    # Get all active cash and bank accounts
    cash_bank_accounts = CashBank.objects.filter(is_active=True)
    total_cash = cash_bank_accounts.filter(account_type='cash').aggregate(
        total=Coalesce(Sum('balance'), Decimal('0'))
    )['total'] or Decimal('0')
    total_bank = cash_bank_accounts.filter(account_type='bank').aggregate(
        total=Coalesce(Sum('balance'), Decimal('0'))
    )['total'] or Decimal('0')
    cash_bank_total = total_cash + total_bank
    
    # ============================================================
    # TOTAL ASSETS
    # ============================================================
    total_assets_amount = (
        ornaments_total +
        raw_gold +
        raw_silver +
        stones_total +
        motimala_total +
        potey_total +
        order_receivable +
        sundry_debtor_total +
        cash_bank_total
    )
    
    context = {
        # Ornaments
        'ornaments_gold': total_gold_amount,
        'ornaments_silver': total_silver_amount,
        'ornaments_diamond': total_diamond_value,
        'ornaments_total': ornaments_total,
        'ornament_count': ornament_count,
        'total_gold_weight': total_gold_weight,
        'total_silver_weight': total_silver_weight,
        'total_diamond_weight': total_diamond_weight,
        'gold_24k_equivalent': gold_24k_equivalent,
        'silver_24k_equivalent': silver_24k_equivalent,
        'diamond_24k_equivalent': diamond_24k_equivalent,
        
        # Raw metals
        'raw_gold': raw_gold,
        'raw_silver': raw_silver,
        'raw_gold_weight': raw_gold_weight,
        'raw_silver_weight': raw_silver_weight,
        
        # Raw metals totals (before orders)
        'raw_gold_total': raw_gold_total,
        'raw_silver_total': raw_silver_total,
        'raw_gold_weight_total': raw_gold_weight_total,
        'raw_silver_weight_total': raw_silver_weight_total,
        
        # Raw metals used in orders
        'order_gold_weight_24k': order_gold_weight_24k,
        'order_silver_weight_24k': order_silver_weight_24k,
        'order_gold_value': order_gold_value,
        'order_silver_value': order_silver_value,
        
        # Other inventory
        'stones_total': stones_total,
        'motimala_total': motimala_total,
        'potey_total': potey_total,
        
        # Receivables
        'order_receivable': order_receivable,
        'sundry_debtor_total': sundry_debtor_total,
        
        # Cash and Bank
        'total_cash': total_cash,
        'total_bank': total_bank,
        'cash_bank_total': cash_bank_total,
        
        # Totals
        'total_assets': total_assets_amount,
        
        # Rates
        'gold_rate': gold_rate,
        'silver_rate': silver_rate,
    }
    
    return render(request, 'main/total_assets.html', context)
