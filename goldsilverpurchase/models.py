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

    RATE_UNIT_CHOICES = [
        ('gram', 'Per Gram'),
        ('10gram', 'Per 10 Gram'),
        ('tola', 'Per Tola'),
    ]

    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'
        BANK_TRANSFER = 'bank', 'Bank Transfer'
        FONEPAY = 'fonepay', 'Fonepay'

    class Purity(models.TextChoices):
        TWENTYFOURKARAT = '24K', '24 Karat'
        TWENTYTWOKARAT = '22K', '22 Karat'
        EIGHTEENKARAT = '18K', '18 Karat'
        FOURTEENKARAT = '14K', '14 Karat'

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

    purity = models.CharField(
        max_length=5,
        choices=Purity.choices,
        default=Purity.TWENTYFOURKARAT,
        help_text='Purity/Karat of the metal'
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

    rate_unit = models.CharField(
        max_length=10,
        choices=RATE_UNIT_CHOICES,
        default='tola',
        help_text='Unit for rate (per gram, per 10 gram, per tola)'
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
        # Conversion constant: 1 tola = 11.6643 grams
        TOLA_TO_GRAM = Decimal('11.6643')
        
        # Ensure Decimal values
        if isinstance(self.quantity, (int, float)):
            self.quantity = Decimal(str(self.quantity))
        self.rate = self.rate or Decimal('0.00')
        self.wages = self.wages or Decimal('0.00')
        self.discount = self.discount or Decimal('0.00')
        
        # Ensure rate_unit is set (don't let it be auto-changed)
        if not self.rate_unit:
            self.rate_unit = 'tola'  # Default only if empty

        # Calculate amount based on rate_unit
        # Quantity is always in grams
        if self.rate_unit == 'gram':
            # Rate is per gram, quantity is in grams
            # Amount = quantity * rate
            calculated_amount = self.quantity * self.rate
        elif self.rate_unit == '10gram':
            # Rate is per 10 grams, quantity is in grams
            # Amount = (quantity / 10) * rate
            calculated_amount = (self.quantity / Decimal('10')) * self.rate
        elif self.rate_unit == 'tola':
            # Rate is per tola (11.6643 grams), quantity is in grams
            # Amount = (quantity / 11.6643) * rate
            calculated_amount = (self.quantity / TOLA_TO_GRAM) * self.rate
        else:
            calculated_amount = Decimal('0.00')

        # Calculate final amount with wages and discount
        self.amount = (calculated_amount + self.wages - self.discount).quantize(Decimal('0.01'))

        # Prevent negative amount
        if self.amount < 0:
            self.amount = Decimal('0.00')

        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Calculate subtotal based on rate_unit without wages and discount"""
        TOLA_TO_GRAM = Decimal('11.6643')
        
        if self.rate_unit == 'gram':
            # Rate is per gram
            subtotal = self.quantity * self.rate
        elif self.rate_unit == '10gram':
            # Rate is per 10 grams
            subtotal = (self.quantity / Decimal('10')) * self.rate
        elif self.rate_unit == 'tola':
            # Rate is per tola
            subtotal = (self.quantity / TOLA_TO_GRAM) * self.rate
        else:
            subtotal = Decimal('0.00')
        
        return subtotal.quantize(Decimal('0.01'))
    
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

    RATE_UNIT_CHOICES = [
        ('gram', 'Per Gram'),
        ('10gram', 'Per 10 Gram'),
        ('tola', 'Per Tola'),
    ]

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
    rate_unit = models.CharField(
        max_length=10,
        choices=RATE_UNIT_CHOICES,
        default='tola',
        help_text='Unit for rate (per gram, per 10 gram, per tola)'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=Decimal('0.00'), blank=True, null=True, help_text='Auto-calculated: Weight × Rate')
    profit_weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal('-999999.999'))], default=Decimal('0.000'), blank=True, null=True, help_text='Auto-calculated: Refined Weight - Final Weight')
    profit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('-999999.99'))], default=Decimal('0.00'), blank=True, null=True, help_text='Auto-calculated: Profit Weight × Rate (adjusted for rate_unit)')

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
        """Auto-generate SN and calculate amount based on rate_unit"""
        # Conversion constant: 1 tola = 11.6643 grams
        TOLA_TO_GRAM = Decimal('11.6643')
        
        # Auto-generate SN if not provided
        if not self.sn:
            all_purchases = CustomerPurchase.objects.all().values_list('sn', flat=True)
            numeric_sns = []
            for sn in all_purchases:
                if sn and str(sn).isdigit():
                    numeric_sns.append(int(sn))
            
            if numeric_sns:
                last_num = max(numeric_sns)
                self.sn = str(last_num + 1)
            else:
                self.sn = "1"
        
        # Ensure Decimal values
        if self.weight is None:
            self.weight = Decimal('0.000')
        elif isinstance(self.weight, (int, float)):
            self.weight = Decimal(str(self.weight))
        
        if self.refined_weight is None:
            self.refined_weight = Decimal('0.000')
        elif isinstance(self.refined_weight, (int, float)):
            self.refined_weight = Decimal(str(self.refined_weight))
        
        if self.percentage is None:
            self.percentage = Decimal('0.00')
        elif isinstance(self.percentage, (int, float)):
            self.percentage = Decimal(str(self.percentage))
        
        self.rate = self.rate or Decimal('0.00')
        
        # Ensure rate_unit is set (don't let it be auto-changed)
        if not self.rate_unit:
            self.rate_unit = 'tola'  # Default only if empty
        
        # Calculate final_weight: weight - (weight * percentage / 100)
        percentage_val = self.percentage or Decimal('0.00')
        self.final_weight = (self.weight - (self.weight * percentage_val / Decimal('100'))).quantize(Decimal('0.001'))
        
        # Calculate profit_weight: refined_weight - final_weight
        self.profit_weight = (self.refined_weight - self.final_weight).quantize(Decimal('0.001'))
        
        # Calculate amount based on rate_unit
        # Final weight is in grams
        if self.rate_unit == 'gram':
            # Rate is per gram, final_weight is in grams
            # Amount = final_weight * rate
            calculated_amount = self.final_weight * self.rate
        elif self.rate_unit == '10gram':
            # Rate is per 10 grams, final_weight is in grams
            # Amount = (final_weight / 10) * rate
            calculated_amount = (self.final_weight / Decimal('10')) * self.rate
        elif self.rate_unit == 'tola':
            # Rate is per tola (11.6643 grams), final_weight is in grams
            # Amount = (final_weight / 11.6643) * rate
            calculated_amount = (self.final_weight / TOLA_TO_GRAM) * self.rate
        else:
            calculated_amount = Decimal('0.00')

        # Set amount
        self.amount = calculated_amount.quantize(Decimal('0.01'))

        # Prevent negative amount
        if self.amount < 0:
            self.amount = Decimal('0.00')
        
        # Calculate profit based on profit_weight and rate_unit
        if self.rate_unit == 'gram':
            calculated_profit = self.profit_weight * self.rate
        elif self.rate_unit == '10gram':
            calculated_profit = (self.profit_weight / Decimal('10')) * self.rate
        elif self.rate_unit == 'tola':
            calculated_profit = (self.profit_weight / TOLA_TO_GRAM) * self.rate
        else:
            calculated_profit = Decimal('0.00')

        # Set profit
        self.profit = calculated_profit.quantize(Decimal('0.01'))
        
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

    RATE_UNIT_CHOICES = [
        ('gram', 'Per Gram'),
        ('10gram', 'Per 10 Gram'),
        ('tola', 'Per Tola'),
    ]

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
        help_text='Cost per selected unit'
    )

    rate_unit = models.CharField(
        max_length=10,
        choices=RATE_UNIT_CHOICES,
        default='tola',
        help_text='Unit for rate (per gram, per 10 gram, per tola)'
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

    class LocationChoices(models.TextChoices):
        GOLD_SILVER_PURCHASE = 'GoldSilverPurchase', 'Gold/Silver Purchase'
        CUSTOMER_PURCHASE = 'CustomerPurchase', 'Customer Purchase'

    location = models.CharField(
        max_length=32,
        choices=LocationChoices.choices,
        default=LocationChoices.GOLD_SILVER_PURCHASE,
        help_text='Source of this stock: Gold/Silver Purchase or Customer Purchase.'
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
        constraints = [
            models.UniqueConstraint(fields=['metal_type', 'stock_type'], name='unique_metaltype_stocktype')
        ]
        indexes = [
            models.Index(fields=['metal_type', 'stock_type']),
            models.Index(fields=['metal_type', 'purity']),
            models.Index(fields=['stock_type']),
        ]

    def __str__(self):
        stock_type_display = self.stock_type.get_name_display() if self.stock_type else 'Unknown'
        return f"{self.get_metal_type_display()} - {stock_type_display} ({self.purity})"

    def save(self, *args, **kwargs):
        """Set unit_cost to the average rate of 'in' MetalStockMovement, then calculate total cost."""
        from decimal import Decimal, ROUND_HALF_UP
        # Ensure Decimal values
        if isinstance(self.quantity, (int, float)):
            self.quantity = Decimal(str(self.quantity))

        # Only calculate averages if PK exists (object is saved)
        if self.pk:
            in_movements = self.movements.filter(movement_type='in')
            total_qty = Decimal('0.00')
            total_cost = Decimal('0.00')
            for m in in_movements:
                if m.rate and m.quantity:
                    total_qty += m.quantity
                    total_cost += m.rate * m.quantity
            if total_qty > 0:
                avg_rate = (total_cost / total_qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                self.unit_cost = avg_rate
            else:
                self.unit_cost = Decimal('0.00')

            # Calculate total cost based on unit_cost and rate_unit
            per_gram_cost = self.unit_cost
            if self.rate_unit == '10gram':
                per_gram_cost = (self.unit_cost or Decimal('0')) / Decimal('10')
            elif self.rate_unit == 'tola':
                per_gram_cost = (self.unit_cost or Decimal('0')) / Decimal('11.6643')

            # Calculate total cost (quantity is in grams)
            self.total_cost = (self.quantity * per_gram_cost).quantize(Decimal('0.01'))

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

    @property
    def unit_cost_per_tola(self):
        """Get unit cost converted to per-tola"""
        if self.rate_unit == 'tola':
            return self.unit_cost
        elif self.rate_unit == '10gram':
            return (self.unit_cost * Decimal('10'))
        elif self.rate_unit == 'gram':
            return (self.unit_cost * Decimal('11.6643'))
        return Decimal('0.00')

    @property
    def get_rate_unit_display_with_tola(self):
        """Get display text with tola value"""
        return f"{self.get_rate_unit_display()} (₹{self.unit_cost_per_tola:.2f}/tola)"


class MetalStockMovement(models.Model):
    """Model to track all movements (additions/deductions) of metal stock"""
    rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=Decimal('0.00'),
        help_text='Rate for this transaction (per selected unit)',
        blank=True,
        null=True
    )
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