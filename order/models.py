from django.db import models
from django.core.validators import RegexValidator
from nepali_datetime_field.models import NepaliDateField
from decimal import Decimal


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('fonepay', 'Fonepay'),
        ('bank', 'Bank'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
    ]

    STATUS_CHOICES = [
        ('order', 'Order'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
    ]
    
    sn = models.AutoField(primary_key=True)
    order_date = NepaliDateField(null=True, blank=True)
    deliver_date = NepaliDateField(null=True, blank=True)
    customer_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\d{7,15}$',
            message='Phone number must be 7-15 digits.',
            code='invalid_phone'
        )],
        help_text='Enter a valid phone number (7-15 digits).'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='order')


    discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text='Discount amount'
    )

    # Amount: sum of all ornaments before discount
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text='Amount of all ornaments before discount'
    )

    # Subtotal: amount minus discount (before tax)
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text='Subtotal after discount and before tax'
    )

    tax = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text='Tax amount'
    )
    
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date', '-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"
    
    def __str__(self):
        return f"Order {self.sn} - {self.customer_name}"
    
    def clean(self):
        """Validate order data."""
        from django.core.exceptions import ValidationError
        
        if self.payment_amount and self.total and self.payment_amount > self.total:
            raise ValidationError("Payment amount cannot exceed total order amount.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def recompute_totals_from_lines(self):
        """Recalculate amount/subtotal/total/remaining based on OrderOrnament lines.

        - amount = sum of line_amount from all related order_ornaments
        - subtotal = max(0, amount - discount)
        - total = subtotal + tax
        - remaining_amount = max(0, total - payment_amount)
        """
        from decimal import Decimal as _D

        line_sum = sum(
            (line.line_amount or _D("0")) for line in self.order_ornaments.all()
        )

        self.amount = line_sum

        # Ensure discount and tax are non-null decimals
        discount = self.discount or _D("0")
        tax = self.tax or _D("0")
        payment = self.payment_amount or _D("0")

        self.subtotal = max(_D("0"), line_sum - discount)
        self.total = self.subtotal + tax
        self.remaining_amount = max(_D("0"), self.total - payment)

        # Persist changes without re-triggering clean logic again unnecessarily
        super().save(update_fields=[
            "amount",
            "subtotal",
            "total",
            "remaining_amount",
            "updated_at",
        ])


class OrderOrnament(models.Model):
    """Per-order ornament line with rates and labour details."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_ornaments",
    )

    ornament = models.ForeignKey(
        "ornament.Ornament",
        on_delete=models.PROTECT,
        related_name="order_lines",
    )

    gold_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Gold rate per unit",
    )

    diamond_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Diamond rate per unit",
    )

    zircon_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Zircon rate per unit",
    )

    stone_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Stone rate per unit",
    )

    # Rate and material fields specific to this order line
    jarti = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Jarti amount",
    )

    jyala = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Jyala amount",
    )

    line_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Line total for this ornament on this order",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order Ornament"
        verbose_name_plural = "Order Ornaments"

    def __str__(self):
        return f"Order {self.order_id} - {self.ornament}"

