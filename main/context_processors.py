from main.models import DailyRate


def latest_rate(request):
    """Provide the most recent DailyRate to all templates."""
    rate = DailyRate.objects.order_by('-created_at').first()
    return {'latest_rate': rate}
