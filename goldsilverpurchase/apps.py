from django.apps import AppConfig


class GoldsilverpurchaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'goldsilverpurchase'
    
    def ready(self):
        """Import signals when app is ready"""
        import goldsilverpurchase.signals
