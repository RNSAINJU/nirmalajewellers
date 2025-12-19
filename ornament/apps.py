from django.apps import AppConfig


class OrnamentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ornament'
    
    def ready(self):
        # Import signal handlers to ensure they are registered when the app is loaded
        try:
            import ornament.signals  # noqa: F401
        except Exception:
            # Avoid raising on import errors during manage.py commands that don't need signals
            pass

