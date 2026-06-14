from main.models import DailyRate


def latest_rate(request):
    """Provide the most recent DailyRate to all templates."""
    rate = DailyRate.objects.order_by('-created_at').first()
    return {'latest_rate': rate}


def customer_nav(request):
    """Shared sidebar navigation data for customer storefront templates."""
    path = request.path
    if path.startswith(('/admin-dashboard', '/accounts', '/finance', '/ornament', '/order', '/sales', '/gsp')):
        return {}

    from ornament.models import Ornament, MainCategory

    categories_by_metal = []
    metal_type_pages = []

    for metal_key, metal_label in Ornament.MetalTypeCategory.choices:
        metal_products = Ornament.objects.filter(
            ornament_type='stock',
            status='active',
            metal_type=metal_key,
        )

        if metal_products.exists():
            metal_type_pages.append({
                'value': metal_key,
                'label': metal_label,
            })

        metal_categories = MainCategory.objects.filter(
            ornament__ornament_type='stock',
            ornament__status='active',
            ornament__metal_type=metal_key,
            ornament__maincategory__isnull=False,
        ).distinct().order_by('name')

        if metal_categories.exists():
            categories_by_metal.append({
                'metal_type': metal_label,
                'categories': metal_categories,
            })

    return {
        'customer_categories_by_metal': categories_by_metal,
        'customer_metal_type_pages': metal_type_pages,
        'customer_nav_tab': '',
    }
