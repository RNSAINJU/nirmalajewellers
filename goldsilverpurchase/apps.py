from django.apps import AppConfig


class GoldsilverpurchaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'goldsilverpurchase'
    
    def ready(self):
        """Import signals when app is ready"""
        self._apply_nepali_calendar_overrides()
        import goldsilverpurchase.signals

    @staticmethod
    def _apply_nepali_calendar_overrides():
        import nepali_datetime

        month_lengths_2082 = [31, 31, 32, 31, 31, 30, 30, 30, 30, 30, 30, 30]
        cumulative_days = [-1]
        total_days = 0
        for days_in_month in month_lengths_2082:
            total_days += days_in_month
            cumulative_days.append(total_days)

        nepali_datetime._CALENDAR[2082] = cumulative_days
