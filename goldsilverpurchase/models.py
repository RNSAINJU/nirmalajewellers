from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from nepali_datetime_field.models import NepaliDateField
from decimal import Decimal

class GoldSilverPurchase(models.Model):
    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'
        UPI = 'upi', 'UPI'
        BANK_TRANSFER = 'bank', 'Bank Transfer'
        OTHER = 'other', 'Other'

    bill_no = models.CharField(max_length=20, unique=True)
    bill_date = NepaliDateField(null=True, blank=True)
    party_name = models.CharField(max_length=255)
    particulars = models.CharField(max_length=255)
    # ... existing code ...

    # updated: digits-only, exactly 9 characters
    panno = models.CharField(
        max_length=9,
        validators=[RegexValidator(
            regex=r'^\d{9}$',
            message='PAN No must be exactly 9 digits.',
            code='invalid_pan_digits'
        )],
        help_text='Enter 9-digit PAN number.'
    )

    particular = models.CharField(max_length=255, blank=True)

    # --- replaced gold_quantity & silver_quantity with a single quantity + metal_type ---
    metal_type = models.CharField(
        max_length=6,
        choices=[('gold', 'Gold'), ('silver', 'Silver')],
        default='gold',
        help_text='Select metal type for this record'
    )

    quantity = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0,
        help_text='Quantity for the selected metal'
    )
    # -------------------------------------------------------------------------------

    rate = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    wages = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=Decimal('0.00')
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=Decimal('0.00')
    )

    payment_mode = models.CharField(
        max_length=12, choices=PaymentMode.choices, default=PaymentMode.CASH
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # removed save() uppercase logic (no longer needed for digits-only)
    def __str__(self):
        return f"{self.bill_no} - {self.party_name}"


    def save(self, *args, **kwargs):
        # normalize blank/None to Decimal('0.00')
        if self.wages in (None, ''):
            self.wages = Decimal('0.00')
        if self.amount in (None, ''):
            self.amount = Decimal('0.00')
            self.amount=(self.quantity / Decimal('11.6638038')) * self.rate + self.wages
            self.amount=self.amount.quantize(Decimal('0.01'))
        return super().save(*args, **kwargs)