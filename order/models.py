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
        ('sundry_debtor', 'Sundry Debtor'),
        ('mixed', 'Mixed'),  # multiple payment modes
    ]

    STATUS_CHOICES = [
        ('order', 'Order'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
    ]

    ORDER_TYPE_CHOICES = [
        ('custom', 'Custom'),
        ('standard', 'Standard'),
        ('repair', 'Repair'),
        ('remake', 'Remake'),
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
    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default='custom',
        help_text='Type of order'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Additional notes or description for the order'
    )


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
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date', '-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"
    
    def __str__(self):
        return f"Order {self.sn} - {self.customer_name}"
    
    @property
    def total_paid(self):
        """Calculate total amount paid from all OrderPayment records."""
        from decimal import Decimal as _D
        payment_sum = sum(
            (p.amount or _D("0")) for p in self.payments.all()
        )
        return payment_sum
    
    def clean(self):
        """Validate order data."""
        from django.core.exceptions import ValidationError
        
        if self.total and self.total < 0:
            raise ValidationError("Total amount cannot be negative.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def recompute_totals_from_lines(self):
        """Recalculate amount/subtotal/total/remaining based on lines and payments.

        - amount = sum of line_amount from all related order_ornaments and order_metals
        - subtotal = max(0, amount - discount)
        - total = subtotal + tax
        - remaining_amount = max(0, total - payment_amount from OrderPayment)
        """
        from decimal import Decimal as _D

        # Sum from both ornaments and metal stock items
        ornament_sum = sum(
            (line.line_amount or _D("0")) for line in self.order_ornaments.all()
        )
        metal_sum = sum(
            (line.line_amount or _D("0")) for line in self.order_metals.all()
        )
        line_sum = ornament_sum + metal_sum

        payment_entries = list(self.payments.all()) if hasattr(self, "payments") else []
        payment_sum = sum((p.amount or _D("0")) for p in payment_entries)

        self.amount = line_sum

        discount = self.discount or _D("0")
        tax = self.tax or _D("0")

        self.subtotal = max(_D("0"), line_sum - discount)
        self.total = self.subtotal + tax

        # Calculate remaining amount based on payments
        self.remaining_amount = max(_D("0"), self.total - payment_sum)

        super().save(update_fields=[
            "amount",
            "subtotal",
            "total",
            "remaining_amount",
            "updated_at",
        ])

    def get_total_metal_weight(self):
        """Get total weight of all metals in the order (in grams)."""
        from decimal import Decimal as _D
        return sum(
            (metal.quantity or _D("0")) for metal in self.order_metals.all()
        )

    def get_metal_weight_by_type(self):
        """Get total weight by metal type (gold, silver, platinum)."""
        from decimal import Decimal as _D
        weight_by_type = {}
        for metal in self.order_metals.all():
            metal_type = metal.get_metal_type_display() or metal.metal_type
            if metal_type not in weight_by_type:
                weight_by_type[metal_type] = _D("0")
            weight_by_type[metal_type] += metal.quantity or _D("0")
        return weight_by_type


class OrderPayment(models.Model):
    """Individual payment entry for an order (supports mixed modes)."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    payment_mode = models.CharField(max_length=20, choices=Order.PAYMENT_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order Payment"
        verbose_name_plural = "Order Payments"

    def __str__(self):
        return f"Payment {self.payment_mode} {self.amount} for Order {self.order_id}"


class DebtorPayment(models.Model):
    """Payment from sundry debtor - links order payment to debtor and tracks balance updates."""

    order_payment = models.OneToOneField(
        OrderPayment,
        on_delete=models.CASCADE,
        related_name="debtor_payment",
        help_text="The order payment this debtor payment is associated with"
    )
    
    debtor = models.ForeignKey(
        "finance.SundryDebtor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_payments",
        help_text="The sundry debtor making this payment"
    )
    
    transaction_type = models.CharField(
        max_length=10,
        choices=[('invoice', 'Invoice'), ('payment', 'Payment')],
        default='invoice',
        help_text="Type of transaction: invoice creates balance, payment reduces it"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Debtor Payment"
        verbose_name_plural = "Debtor Payments"

    def __str__(self):
        if self.debtor:
            return f"Debtor {self.debtor.name} - Order {self.order_payment.order_id} ({self.transaction_type})"
        return f"Debtor Payment - Order {self.order_payment.order_id}"


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



class OrderMetalStock(models.Model):
    """Per-order raw metal (gold/silver) line item with rates and quantities."""

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

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_metals",
        help_text="Associated order"
    )

    stock_type = models.ForeignKey(
        'goldsilverpurchase.MetalStockType',
        on_delete=models.PROTECT,
        related_name='order_metal_stocks',
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
        help_text="Rate per gram at the time of order"
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
        verbose_name = "Order Metal Stock"
        verbose_name_plural = "Order Metal Stocks"
        indexes = [
            models.Index(fields=['order', 'metal_type']),
        ]

    def __str__(self):
        return f"Order {self.order_id} - {self.get_metal_type_display()} ({self.purity}) - {self.quantity}g"

    def save(self, *args, **kwargs):
        """Auto-calculate line amount"""
        # Ensure Decimal values
        if isinstance(self.quantity, (int, float)):
            self.quantity = Decimal(str(self.quantity))
        elif self.quantity is None:
            self.quantity = Decimal('0.00')
            
        self.rate_per_gram = self.rate_per_gram or Decimal('0.00')

        # Calculate line amount
        if self.quantity and self.rate_per_gram:
            self.line_amount = (self.quantity * self.rate_per_gram).quantize(Decimal('0.01'))
        else:
            self.line_amount = Decimal('0.00')

        super().save(*args, **kwargs)
