from django.db import models
from django.core.validators import MinValueValidator, RegexValidator  # added RegexValidator

class GoldSilverPurchase(models.Model):
    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'
        UPI = 'upi', 'UPI'
        BANK_TRANSFER = 'bank', 'Bank Transfer'
        OTHER = 'other', 'Other'

    bill_no = models.CharField(max_length=20, unique=True)
    bill_date = models.DateField()
    party_name = models.CharField(max_length=255)
    # ... existing code ...

    # updated: digits-only, exactly 9 characters
    panno = models.CharField(
        max_length=9,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\d{9}$',
            message='PAN No must be exactly 9 digits.',
            code='invalid_pan_digits'
        )],
        help_text='Enter 9-digit PAN number.'
    )

    particular = models.CharField(max_length=255, blank=True)

    gold_quantity = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    silver_quantity = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    rate = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    wages = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    payment_mode = models.CharField(
        max_length=12, choices=PaymentMode.choices, default=PaymentMode.CASH
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # removed save() uppercase logic (no longer needed for digits-only)
    def __str__(self):
        return f"{self.bill_no} - {self.party_name}"
