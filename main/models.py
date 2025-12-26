from django.db import models
from decimal import Decimal
from datetime import datetime, date

class DailyRate(models.Model):
    """Store daily gold and silver rates from FENEGOSIDA."""
    date = models.DateField(default=date.today, unique=True)
    bs_date = models.CharField(max_length=50, blank=True, help_text="Nepali date as shown on site, e.g., '11 Poush 2082'")

    # Per tola rates
    gold_rate = models.DecimalField(max_digits=12, decimal_places=2, help_text="Gold rate per tola")
    silver_rate = models.DecimalField(max_digits=12, decimal_places=2, help_text="Silver rate per tola")

    # Per 10 gram derived rates
    gold_rate_10g = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Gold rate per 10 grams")
    silver_rate_10g = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Silver rate per 10 grams")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Rates - {self.date} ({self.bs_date})"


class Stock(models.Model):
    """
    Previous year remaining stock details.
    Stores opening balances for Diamond, Gold, Silver, Jardi, and Wages.
    """
    year = models.IntegerField(help_text="Fiscal year (e.g., 2078, 2079)", unique=True)
    diamond = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.000'), help_text="Diamond stock in grams")
    gold = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.000'), help_text="Gold stock in grams")
    silver = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.000'), help_text="Silver stock in grams")
    jardi = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Jardi amount in currency")
    wages = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Wages amount in currency")
    
    # Rates for calculating amounts
    diamond_rate = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Diamond rate per gram")
    gold_rate = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Gold rate per gram")
    silver_rate = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Silver rate per gram")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stock"
        ordering = ['-year']

    def __str__(self):
        return f"Stock - Year {self.year}"
    
    @property
    def diamond_amount(self):
        """Calculate diamond amount based on quantity and rate."""
        return (self.diamond or Decimal("0")) * (self.diamond_rate or Decimal("0"))
    
    @property
    def gold_amount(self):
        """Calculate gold amount based on quantity and rate."""
        return ((self.gold or Decimal("0")) / Decimal("11.664")) * (self.gold_rate or Decimal("0"))
    
    @property
    def silver_amount(self):
        """Calculate silver amount based on quantity and rate."""
        return ((self.silver or Decimal("0")) / Decimal("11.664")) * (self.silver_rate or Decimal("0"))
