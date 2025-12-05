from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from nepali_datetime_field.models import NepaliDateField
from decimal import Decimal


class Party(models.Model):
    party_name = models.CharField(max_length=255)
    panno = models.CharField(
        max_length=9,
        validators=[RegexValidator(
            regex=r'^\d{9}$',
            message='PAN No must be exactly 9 digits.',
            code='invalid_pan_digits'
        )],
        help_text='Enter 9-digit PAN number.'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['party_name', 'panno'], name='unique_party_name_panno')
        ]
        
    def __str__(self):
        return self.party_name


class GoldSilverPurchase(models.Model):

    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'
        UPI = 'upi', 'UPI'
        BANK_TRANSFER = 'bank', 'Bank Transfer'
        OTHER = 'other', 'Other'

    bill_no = models.CharField(max_length=20, unique=True)
    bill_date = NepaliDateField(null=True, blank=True)
    party = models.ForeignKey(
        Party,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gold_purchases',
        help_text='Select the party for this purchase'
    )

    particular = models.CharField(max_length=255, null=True, blank=True)
    metal_type = models.CharField(
        max_length=6,
        choices=[('gold', 'Gold'), ('silver', 'Silver')],
        default='gold'
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
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
        null=True, blank=True,
        default=Decimal('0.00')
    )

    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True, blank=True,
        default=Decimal('0.00')
    )

    payment_mode = models.CharField(
        max_length=12,
        choices=PaymentMode.choices,
        default=PaymentMode.CASH
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bill_no} - {self.particular}"

    def save(self, *args, **kwargs):
        self.wages = self.wages or Decimal('0.00')

        # Calculate amount automatically
        calculated_amount = (self.quantity / Decimal('11.6638038')) * self.rate
        self.amount = (calculated_amount + self.wages).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)
