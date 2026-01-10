"""Order reports and analytics views"""
from django.shortcuts import render
from django.views import View
from django.db.models import Sum, Count, Q, F, DecimalField, Case, When, Value
from django.db.models.functions import Coalesce, TruncMonth, TruncYear
from decimal import Decimal
from datetime import datetime, timedelta
from .models import Order, OrderPayment


class OrderDashboardReport(View):
    """Main order dashboard with key metrics and charts"""
    
    def get(self, request):
        # Date filters
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        orders_qs = Order.objects.all()
        
        if date_from:
            orders_qs = orders_qs.filter(order_date__gte=date_from)
        if date_to:
            orders_qs = orders_qs.filter(order_date__lte=date_to)
        
        # Key metrics
        total_orders = orders_qs.count()
        total_revenue = orders_qs.aggregate(
            total=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
        )['total']
        total_collected = orders_qs.aggregate(
            total=Coalesce(Sum('payment_amount'), Decimal('0'), output_field=DecimalField())
        )['total']
        total_pending = total_revenue - total_collected
        
        # Orders by status
        status_summary = orders_qs.values('status').annotate(
            count=Count('sn'),
            amount=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
        ).order_by('-count')
        
        # Orders by type
        type_summary = orders_qs.values('order_type').annotate(
            count=Count('sn'),
            amount=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
        ).order_by('-count')
        
        # Payment methods summary
        payment_summary = orders_qs.values('payment_mode').annotate(
            count=Count('sn'),
            amount=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
        ).order_by('-count')
        
        # Monthly trend
        monthly_data = orders_qs.annotate(
            month=TruncMonth('order_date')
        ).values('month').annotate(
            count=Count('sn'),
            revenue=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField()),
            collected=Coalesce(Sum('payment_amount'), Decimal('0'), output_field=DecimalField())
        ).order_by('month')
        
        # Top customers by revenue
        top_customers = orders_qs.values('customer_name').annotate(
            order_count=Count('sn'),
            total_amount=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField()),
            paid_amount=Coalesce(Sum('payment_amount'), Decimal('0'), output_field=DecimalField()),
            pending=F('total_amount') - F('paid_amount')
        ).order_by('-total_amount')[:10]
        
        context = {
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'total_collected': float(total_collected),
            'total_pending': float(total_pending),
            'collection_rate': round((float(total_collected) / float(total_revenue) * 100) if total_revenue > 0 else 0, 2),
            'status_summary': list(status_summary),
            'type_summary': list(type_summary),
            'payment_summary': list(payment_summary),
            'monthly_data': list(monthly_data),
            'top_customers': list(top_customers),
            'date_from': date_from,
            'date_to': date_to,
        }
        
        return render(request, 'order/reports/dashboard.html', context)


class OrderSalesAnalysis(View):
    """Detailed sales analysis with profit calculations"""
    
    def get(self, request):
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        order_type = request.GET.get('order_type')
        
        orders_qs = Order.objects.prefetch_related('order_ornaments')
        
        if date_from:
            orders_qs = orders_qs.filter(order_date__gte=date_from)
        if date_to:
            orders_qs = orders_qs.filter(order_date__lte=date_to)
        if order_type:
            orders_qs = orders_qs.filter(order_type=order_type)
        
        # Sales analysis
        total_orders = orders_qs.count()
        total_amount = orders_qs.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0'), output_field=DecimalField())
        )['total']
        total_discount = orders_qs.aggregate(
            total=Coalesce(Sum('discount'), Decimal('0'), output_field=DecimalField())
        )['total']
        total_tax = orders_qs.aggregate(
            total=Coalesce(Sum('tax'), Decimal('0'), output_field=DecimalField())
        )['total']
        total_revenue = orders_qs.aggregate(
            total=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
        )['total']
        
        # Calculate profit (assuming cost is discount amount or markup)
        avg_order_value = float(total_amount) / total_orders if total_orders > 0 else 0
        avg_discount_percent = (float(total_discount) / float(total_amount) * 100) if total_amount > 0 else 0
        
        # Orders by status
        order_details = []
        for order in orders_qs.order_by('-order_date'):
            ornament_count = order.order_ornaments.count()
            metal_count = order.order_metals.count()
            pending = order.total - order.payment_amount
            order_details.append({
                'sn': order.sn,
                'customer_name': order.customer_name,
                'order_date': order.order_date,
                'status': order.get_status_display(),
                'order_type': order.get_order_type_display(),
                'items_count': ornament_count + metal_count,
                'amount': float(order.amount),
                'discount': float(order.discount),
                'tax': float(order.tax),
                'total': float(order.total),
                'paid': float(order.payment_amount),
                'pending': float(pending),
                'collection_percent': round((float(order.payment_amount) / float(order.total) * 100) if order.total > 0 else 0, 2)
            })
        
        context = {
            'total_orders': total_orders,
            'total_amount': float(total_amount),
            'total_discount': float(total_discount),
            'total_tax': float(total_tax),
            'total_revenue': float(total_revenue),
            'avg_order_value': round(avg_order_value, 2),
            'avg_discount_percent': round(avg_discount_percent, 2),
            'order_details': order_details,
            'date_from': date_from,
            'date_to': date_to,
            'order_type': order_type,
        }
        
        return render(request, 'order/reports/sales_analysis.html', context)


class OrderPaymentAnalysis(View):
    """Payment collection and pending analysis"""
    
    def get(self, request):
        orders_qs = Order.objects.all()
        
        # Payment status breakdown
        fully_paid = orders_qs.filter(remaining_amount=0).count()
        partial_paid = orders_qs.filter(remaining_amount__gt=0, payment_amount__gt=0).count()
        unpaid = orders_qs.filter(payment_amount=0).count()
        
        total_pending = orders_qs.aggregate(
            total=Coalesce(Sum('remaining_amount'), Decimal('0'), output_field=DecimalField())
        )['total']
        
        total_collected = orders_qs.aggregate(
            total=Coalesce(Sum('payment_amount'), Decimal('0'), output_field=DecimalField())
        )['total']
        
        total_due = orders_qs.aggregate(
            total=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
        )['total']
        
        # Payment methods
        payment_methods = OrderPayment.objects.values('payment_mode').annotate(
            count=Count('id'),
            amount=Coalesce(Sum('amount'), Decimal('0'), output_field=DecimalField())
        ).order_by('-amount')
        
        # Pending orders
        pending_orders = orders_qs.filter(
            remaining_amount__gt=0
        ).values('customer_name', 'phone_number').annotate(
            order_count=Count('sn'),
            total_pending=Coalesce(Sum('remaining_amount'), Decimal('0'), output_field=DecimalField()),
            total_due=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField()),
            paid=Coalesce(Sum('payment_amount'), Decimal('0'), output_field=DecimalField())
        ).order_by('-total_pending')
        
        # Calculate percentage paid for each customer
        for customer in pending_orders:
            if customer['total_due'] > 0:
                customer['paid_percent'] = round((float(customer['paid']) / float(customer['total_due'])) * 100, 2)
            else:
                customer['paid_percent'] = 0
        
        context = {
            'fully_paid': fully_paid,
            'partial_paid': partial_paid,
            'unpaid': unpaid,
            'total_pending': float(total_pending),
            'total_collected': float(total_collected),
            'total_due': float(total_due),
            'collection_rate': round((float(total_collected) / float(total_due) * 100) if total_due > 0 else 0, 2),
            'payment_methods': list(payment_methods),
            'pending_orders': list(pending_orders),
        }
        
        return render(request, 'order/reports/payment_analysis.html', context)


class OrderMetalAnalysis(View):
    """Metal usage and stock analysis in orders"""
    
    def get(self, request):
        from .models import OrderMetalStock
        
        # Get only orders that have metals
        orders_qs = Order.objects.filter(order_metals__isnull=False).prefetch_related('order_metals').distinct()
        
        total_orders = orders_qs.count()
        
        # Metal summary - aggregate directly from OrderMetalStock
        metal_summary = OrderMetalStock.objects.values('metal_type').annotate(
            total_quantity=Coalesce(Sum('quantity'), Decimal('0'), output_field=DecimalField()),
            total_value=Coalesce(Sum('line_amount'), Decimal('0'), output_field=DecimalField()),
            count=Count('order', distinct=True)
        ).order_by('-total_quantity')
        
        context = {
            'total_orders': total_orders,
            'metal_summary': list(metal_summary),
        }
        
        return render(request, 'order/reports/metal_analysis.html', context)


class OrderCustomerAnalysis(View):
    """Customer analysis and segmentation"""
    
    def get(self, request):
        orders_qs = Order.objects.all()
        
        # Customer metrics
        unique_customers = orders_qs.values('customer_name').distinct().count()
        repeat_customers = orders_qs.values('customer_name').annotate(
            order_count=Count('sn')
        ).filter(order_count__gt=1).count()
        
        # Calculate repeat customer percentage
        repeat_percent = round((repeat_customers / unique_customers * 100) if unique_customers > 0 else 0, 1)
        
        # Customer details
        customer_details = orders_qs.values('customer_name', 'phone_number').annotate(
            order_count=Count('sn'),
            total_spent=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField()),
            paid=Coalesce(Sum('payment_amount'), Decimal('0'), output_field=DecimalField()),
            pending=Coalesce(Sum('remaining_amount'), Decimal('0'), output_field=DecimalField()),
            avg_order_value=Coalesce(Sum('total') / Count('sn'), Decimal('0'), output_field=DecimalField())
        ).order_by('-total_spent')
        
        context = {
            'unique_customers': unique_customers,
            'repeat_customers': repeat_customers,
            'repeat_percent': repeat_percent,
            'customer_details': list(customer_details),
        }
        
        return render(request, 'order/reports/customer_analysis.html', context)
