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
        BANK_TRANSFER = 'bank', 'Bank Transfer'
        FONEPAY = 'fonepay', 'Fonepay'

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
        max_length=10,
        choices=[('gold', 'Gold'), ('silver', 'Silver'),('diamond', 'Diamond')],
        default='gold'
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=Decimal('0.000')
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

    discount = models.DecimalField(
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

    # Status and tracking
    is_paid = models.BooleanField(default=True)
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gold/Silver Purchase"
        verbose_name_plural = "Gold/Silver Purchases"
        ordering = ['-bill_date', '-created_at']
        indexes = [
            models.Index(fields=['bill_no']),
            models.Index(fields=['party', 'bill_date']),
            models.Index(fields=['metal_type', 'bill_date']),
        ]
    
    def __str__(self):
        return f"{self.bill_no} - {self.particular or 'Untitled'}"

    def save(self, *args, **kwargs):
            # Ensure Decimal values
        if isinstance(self.quantity, (int, float)):
            self.quantity = Decimal(str(self.quantity))
        self.rate = self.rate or Decimal('0.00')
        self.wages = self.wages or Decimal('0.00')
        self.discount = self.discount or Decimal('0.00')

        # Calculate amount automatically
        calculated_amount = self.quantity  * self.rate
        self.amount = (calculated_amount + self.wages - self.discount).quantize(Decimal('0.01'))

        # Optional: prevent negative amount
        if self.amount < 0:
            self.amount = Decimal('0.00')

        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Calculate subtotal without wages and discount"""
        return (self.quantity * self.rate).quantize(Decimal('0.01'))
    
    # @property
    # def total_weight(self):
    #     """Get total weight in grams"""
    #     return self.quantity  # Already in grams if that's your unit
    
    # @property
    # def net_amount(self):
    #     """Calculate net amount (same as amount field)"""
    #     return (self.subtotal + self.wages - self.discount).quantize(Decimal('0.01'))
    
    # def clean(self):
    #     """Additional validation"""
    #     from django.core.exceptions import ValidationError
        
    #     # Ensure quantity is positive if rate is positive
    #     if self.rate > 0 and self.quantity <= 0:
    #         raise ValidationError({
    #             'quantity': 'Quantity must be greater than 0 when rate is positive.'
    #         })
        
    #     # Ensure discount doesn't exceed subtotal + wages
    #     max_discount = self.subtotal + self.wages
    #     if self.discount > max_discount:
    #         raise ValidationError({
    #             'discount': f'Discount cannot exceed {max_discount}.'
    #         })


class CustomerPurchase(models.Model):
    class MetalType(models.TextChoices):
        GOLD = 'gold', 'Gold'
        SILVER = 'silver', 'Silver'
        DIAMOND = 'diamond', 'Diamond'

    id = models.AutoField(primary_key=True)
    sn = models.CharField(max_length=20, unique=True, verbose_name="SN", blank=True)
    purchase_date = NepaliDateField(null=True, blank=True)
    customer_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    phone_no = models.CharField(max_length=20, blank=True, null=True)
    metal_type = models.CharField(max_length=10, choices=MetalType.choices, default=MetalType.GOLD)
    ornament_name = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], default=Decimal('0.000'))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)], default=Decimal('0.00'), blank=True, null=True, help_text='Percentage of weight (e.g., for loss calculation)')
    final_weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], default=Decimal('0.000'), blank=True, null=True, help_text='Final weight after applying percentage')
    refined_weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], default=Decimal('0.000'))
    rate = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=Decimal('0.00'))
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=Decimal('0.00'), blank=True, null=True, help_text='Auto-calculated: Weight × Rate')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sn']
        indexes = [
            models.Index(fields=['sn']),
            models.Index(fields=['customer_name']),
            models.Index(fields=['purchase_date']),
        ]

    def __str__(self):
        return f"{self.sn} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        """Auto-generate SN serially in descending order if not provided."""
        if not self.sn:
            # Get all SNs, convert to integers, and find the maximum
            all_purchases = CustomerPurchase.objects.all().values_list('sn', flat=True)
            numeric_sns = []
            for sn in all_purchases:
                if sn and str(sn).isdigit():
                    numeric_sns.append(int(sn))
            
            if numeric_sns:
                last_num = max(numeric_sns)
                self.sn = str(last_num + 1)
            else:
                # Start from 1 if no previous records
                self.sn = "1"
        
        super().save(*args, **kwargs)


class MetalStockType(models.Model):
    """Model to define different types of metal stock"""
    class StockTypeChoices(models.TextChoices):
        RAW = 'raw', 'Raw'
        REFINED = 'refined', 'Refined'
        SCRAP = 'scrap', 'Scrap'
        OTHER = 'other', 'Other'

    name = models.CharField(
        max_length=20,
        choices=StockTypeChoices.choices,
        unique=True
    )
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Metal Stock Type"
        verbose_name_plural = "Metal Stock Types"

    def __str__(self):
        return self.get_name_display()


class MetalStock(models.Model):
    """Model to track gold and silver stock with raw and refined variants"""
    class MetalType(models.TextChoices):
        GOLD = 'gold', 'Gold'
        SILVER = 'silver', 'Silver'
        PLATINUM = 'platinum', 'Platinum'

    class Purity(models.TextChoices):
        TWENTYFOURKARAT = '24K', '24 Karat'
        TWENTYTWOKARAT = '22K', '22 Karat'
        EIGHTEENKARAT = '18K', '18 Karat'
        FOURTEENKARAT = '14K', '14 Karat'

    # Core fields
    metal_type = models.CharField(
        max_length=10,
        choices=MetalType.choices,
        default=MetalType.GOLD
    )
    stock_type = models.ForeignKey(
        MetalStockType,
        on_delete=models.PROTECT,
        related_name='metal_stocks',
        help_text='Type of stock: Raw or Refined'
    )
    purity = models.CharField(
        max_length=5,
        choices=Purity.choices,
        default=Purity.TWENTYTWOKARAT,
        help_text='Purity/Karat of the metal'
    )

    # Quantity tracking
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=Decimal('0.000'),
        help_text='Weight in grams'
    )

    # Cost tracking
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=Decimal('0.00'),
        help_text='Cost per gram'
    )

    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=Decimal('0.00'),
        blank=True,
        null=True,
        help_text='Auto-calculated: Quantity × Unit Cost'
    )

    # Location/Storage
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Storage location (e.g., Safe, Almirah, etc.)'
    )

    # Remarks and notes
    remarks = models.TextField(
        blank=True,
        null=True,
        help_text='Additional notes about the stock'
    )

    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Metal Stock"
        verbose_name_plural = "Metal Stocks"
        ordering = ['-last_updated', '-created_at']
        indexes = [
            models.Index(fields=['metal_type', 'stock_type']),
            models.Index(fields=['metal_type', 'purity']),
            models.Index(fields=['stock_type']),
        ]

    def __str__(self):
        stock_type_display = self.stock_type.get_name_display() if self.stock_type else 'Unknown'
        return f"{self.get_metal_type_display()} - {stock_type_display} ({self.purity})"

    def save(self, *args, **kwargs):
        """Auto-calculate total cost"""
        # Ensure Decimal values
        if isinstance(self.quantity, (int, float)):
            self.quantity = Decimal(str(self.quantity))
        self.unit_cost = self.unit_cost or Decimal('0.00')

        # Calculate total cost
        self.total_cost = (self.quantity * self.unit_cost).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        """Check if stock is running low (can be customized)"""
        # You can define a minimum threshold per metal type
        minimum_thresholds = {
            'gold': Decimal('50.000'),
            'silver': Decimal('200.000'),
            'platinum': Decimal('10.000'),
        }
        threshold = minimum_thresholds.get(self.metal_type, Decimal('0.000'))
        return self.quantity < threshold


class MetalStockMovement(models.Model):
    """Model to track all movements (additions/deductions) of metal stock"""
    class MovementType(models.TextChoices):
        IN = 'in', 'Stock In'
        OUT = 'out', 'Stock Out'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    metal_stock = models.ForeignKey(
        MetalStock,
        on_delete=models.CASCADE,
        related_name='movements'
    )
    movement_type = models.CharField(
        max_length=15,
        choices=MovementType.choices,
        default=MovementType.IN
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text='Weight moved (in grams)'
    )

    # Reference to the transaction
    reference_type = models.CharField(
        max_length=50,
        help_text='e.g., Purchase, Sale, Refinement, Conversion',
        blank=True,
        null=True
    )
    reference_id = models.CharField(
        max_length=100,
        help_text='Bill number or transaction ID',
        blank=True,
        null=True
    )

    # Details
    notes = models.TextField(blank=True, null=True)
    movement_date = NepaliDateField(blank=True, null=True, help_text='Date of the stock movement')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Metal Stock Movement"
        verbose_name_plural = "Metal Stock Movements"
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['metal_stock', 'movement_date']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        try:
            return f"{self.get_movement_type_display()} - {self.metal_stock} ({float(self.quantity)}g)"
        except (TypeError, ValueError):
            return f"Movement #{self.pk or 'New'}"