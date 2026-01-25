from django.http import JsonResponse
from goldsilverpurchase.models import MetalStock

def get_metal_stock_balance(request):
    stock_type_id = request.GET.get('stock_type_id')
    metal_type = request.GET.get('metal_type')
    purity = request.GET.get('purity')
    if not (stock_type_id and metal_type and purity):
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    try:
        stock = MetalStock.objects.filter(
            stock_type_id=stock_type_id,
            metal_type=metal_type,
            purity=purity
        ).first()
        balance = float(stock.quantity) if stock else 0.0
        return JsonResponse({'balance': balance})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
