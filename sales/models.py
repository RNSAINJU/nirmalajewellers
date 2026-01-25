from django.db import models
from nepali_datetime_field.models import NepaliDateField

from order.models import Order


class Sale(models.Model):
    """Represents a finalized sale created from an Order.

    Physically lives in the `sales` app, but logically belongs to the
    `order` app (via `app_label`) so existing migrations and the database
    table continue to work unchanged.
    """

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="sale",
    )

    # Date when the sale is recorded (typically deliver_date or today)
    sale_date = NepaliDateField(null=True, blank=True)

    # Optional separate bill number for the sale
    bill_no = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "order"  # keep model under the `order` app for migrations
        db_table = "order_sale"  # reuse existing table name
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ["-sale_date", "-created_at"]

    def __str__(self):
        return f"Sale for Order {self.order_id}"


# --- Raw Metal Stock for Sales ---
from goldsilverpurchase.models import MetalStockType, MetalStock
from decimal import Decimal


class SalesMetalStock(models.Model):
    """Per-sale raw metal (gold/silver) line item with rates and quantities."""

    RATE_UNIT_CHOICES = [
        ('gram', 'Per Gram'),
        ('10gram', 'Per 10 Gram'),
        ('tola', 'Per Tola'),
    ]

    rate_unit = models.CharField(
        max_length=10,
        choices=RATE_UNIT_CHOICES,
        default='gram',
        help_text='Unit for rate (per gram, per 10 gram, per tola)'
    )

    class MetalType(models.TextChoices):
        GOLD = 'gold', 'Gold'
        SILVER = 'silver', 'Silver'
        PLATINUM = 'platinum', 'Platinum'

    class Purity(models.TextChoices):
        TWENTYFOURKARAT = '24K', '24 Karat'
        TWENTYTWOKARAT = '22K', '22 Karat'
        EIGHTEENKARAT = '18K', '18 Karat'
        FOURTEENKARAT = '14K', '14 Karat'

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="sale_metals",
        help_text="Associated sale"
    )

    stock_type = models.ForeignKey(
        MetalStockType,
        on_delete=models.PROTECT,
        related_name='sales_metal_stocks',
        help_text='Type of stock: Raw, Refined, Scrap, Other',
        null=True,
        blank=True
    )

    metal_type = models.CharField(
        max_length=10,
        choices=MetalType.choices,
        default=MetalType.GOLD,
        help_text="Type of metal"
    )

    purity = models.CharField(
        max_length=5,
        choices=Purity.choices,
        default=Purity.TWENTYFOURKARAT,
        help_text="Purity/Karat of the metal"
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Quantity in grams"
    )

    rate_per_gram = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Rate per gram at the time of sale"
    )

    line_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        null=True,
        help_text="Auto-calculated: Quantity × Rate per gram"
    )

    remarks = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this metal item"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sales Metal Stock"
        verbose_name_plural = "Sales Metal Stocks"
        indexes = [
            models.Index(fields=['sale', 'metal_type']),
        ]

    def __str__(self):
        return f"Sale {self.sale_id} - {self.get_metal_type_display()} ({self.purity}) - {self.quantity}g"

    def save(self, *args, **kwargs):
        """Auto-calculate line amount based on rate_unit."""
        # Ensure Decimal values
        if isinstance(self.quantity, (int, float)):
            self.quantity = Decimal(str(self.quantity))
        elif self.quantity is None:
            self.quantity = Decimal('0.00')
        self.rate_per_gram = self.rate_per_gram or Decimal('0.00')

        qty = self.quantity or Decimal('0.00')
        rate = self.rate_per_gram or Decimal('0.00')
        unit = self.rate_unit or 'gram'
        if qty and rate:
            if unit == 'gram':
                self.line_amount = (qty * rate).quantize(Decimal('0.01'))
            elif unit == '10gram':
                self.line_amount = ((qty / Decimal('10')) * rate).quantize(Decimal('0.01'))
            elif unit == 'tola':
                self.line_amount = ((qty / Decimal('11.664')) * rate).quantize(Decimal('0.01'))
            else:
                self.line_amount = (qty * rate).quantize(Decimal('0.01'))
        else:
            self.line_amount = Decimal('0.00')
        super().save(*args, **kwargs)
        super().save(*args, **kwargs)
