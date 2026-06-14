from main.models import DailyRate, CustomerPageImage


def latest_rate(request):
    """Provide the most recent DailyRate to all templates."""
    rate = DailyRate.objects.order_by('-created_at').first()
    return {'latest_rate': rate}


def site_branding(request):
    """Provide dynamic site logo URL for customer and admin templates."""
    logo = CustomerPageImage.get_for_slot(CustomerPageImage.PageSlot.SITE_LOGO)
    return {'site_logo_url': logo.image_url}
