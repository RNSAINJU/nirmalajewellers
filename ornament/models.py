from django.db import models
# Stone Model
class Stone(models.Model):
    name = models.CharField(max_length=255)
    cost_per_carat = models.DecimalField(max_digits=10, decimal_places=2)
    carat = models.DecimalField(max_digits=10, decimal_places=3)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    sales_per_carat = models.DecimalField(max_digits=10, decimal_places=2)
    sales_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    profit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.cost_price = (self.cost_per_carat or 0) * (self.carat or 0)
        self.sales_price = (self.sales_per_carat or 0) * (self.carat or 0)
        self.profit = (self.sales_price or 0) - (self.cost_price or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# Motimala Model
class Motimala(models.Model):
    name = models.CharField(max_length=255)
    cost_per_mala = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    sales_per_mala = models.DecimalField(max_digits=10, decimal_places=2)
    sales_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    profit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.cost_price = (self.cost_per_mala or 0) * (self.quantity or 0)
        self.sales_price = (self.sales_per_mala or 0) * (self.quantity or 0)
        self.profit = (self.sales_price or 0) - (self.cost_price or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# Potey Model
class Potey(models.Model):
    name = models.CharField(max_length=255)
    loon = models.PositiveIntegerField()
    cost_per_loon = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    sales_per_loon = models.DecimalField(max_digits=10, decimal_places=2)
    sales_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    profit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.cost_price = (self.cost_per_loon or 0) * (self.loon or 0)
        self.sales_price = (self.sales_per_loon or 0) * (self.loon or 0)
        self.profit = (self.sales_price or 0) - (self.cost_price or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
from datetime import date
from decimal import Decimal
from os import name
from django.db import models
from nepali_datetime_field.models import NepaliDateField
from django.core.validators import MinValueValidator, RegexValidator
from cloudinary.models import CloudinaryField

class MainCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Kaligar(models.Model):
    name = models.CharField(max_length=255)
    phone_no = models.CharField(max_length=20, blank=True, null=True)
    panno = models.CharField(
        max_length=9,
        validators=[RegexValidator(
            regex=r'^\d{9}$',
            message='PAN No must be exactly 9 digits.',
            code='invalid_pan_digits'
        )],
        help_text='Enter 9-digit PAN number.'
    )
    address = models.CharField(max_length=255, blank=True, null=True)
    stamp = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Kaligar_Ornaments(models.Model):

    class TypeCategory(models.TextChoices):
        TWENTYFOURKARAT = '24KARAT', '24 Karat'
        TWENTYTWOKARAT = '22KARAT', '22 Karat'
        EIGHTEENKARAT = '18KARAT', '18 Karat'
        FOURTEENKARAT = '14KARAT', '14 Karat'

    date=NepaliDateField(null=True, blank=True)
    gold_given=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    ornament_weight=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    jarti=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    gold_return=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    gold_loss=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    gold_purity=models.CharField(
        max_length=10,
        choices=TypeCategory.choices,
        default=TypeCategory.TWENTYFOURKARAT,
        verbose_name="किसिम",
    )
    kaligar = models.ForeignKey(Kaligar, on_delete=models.CASCADE, related_name="kaligar_ornaments")

class Kaligar_CashAccount(models.Model):
    date=NepaliDateField(null=True, blank=True)
    particular=models.CharField(max_length=255)
    amount_taken=models.IntegerField()
    to_pay=models.IntegerField()
    provided_by= models.CharField(max_length=255)
    kaligar = models.ForeignKey(Kaligar, on_delete=models.CASCADE, related_name="cash_accounts")


class Kaligar_GoldAccount(models.Model):
    date=NepaliDateField(null=True, blank=True)
    gold_deposit=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    gold_loss=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    gold_remaining=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    kaligar = models.ForeignKey(Kaligar, on_delete=models.CASCADE, related_name="gold_accounts")


class Kaligar_LossReturn(models.Model):
    date = NepaliDateField(null=True, blank=True)
    gold_loss = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    gold_return = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    remark = models.CharField(max_length=255, blank=True, null=True)
    kaligar = models.ForeignKey(Kaligar, on_delete=models.CASCADE, related_name="loss_returns")


class Ornament(models.Model):
    """Ornament master for stock/order tracking."""

    class OrnamentCategory(models.TextChoices):
        STOCK = 'stock', 'Stock'
        ORDER = 'order', 'Order'
        SALES = 'sales', 'Sales'

    class TypeCategory(models.TextChoices):
        TWENTYFOURKARAT = '24KARAT', '24 Karat'
        TWENTHREEKARAT = '23KARAT', '23 Karat'
        TWENTYTWOKARAT = '22KARAT', '22 Karat'
        EIGHTEENKARAT = '18KARAT', '18 Karat'
        FOURTEENKARAT = '14KARAT', '14 Karat'
    
    class MetalTypeCategory(models.TextChoices):
        GOLD = 'Gold', 'Gold'
        SILVER = 'Silver', 'Silver'
        DIAMOND = 'Diamond', 'Diamond'
        OTHERS = 'Others', 'Others'

    class StatusCategory(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DELETED = 'deleted', 'Deleted'
        DESTROYED = 'destroyed', 'Destroyed'

    ornament_date = NepaliDateField(null=True, blank=True)
    code = models.CharField(max_length=50, verbose_name="Code / नं.", null=True, blank=True, unique=True)
    barcode = models.CharField(max_length=50, verbose_name="Barcode", null=True, blank=True, unique=True)
    metal_type=models.CharField(
        max_length=50,
        choices=MetalTypeCategory.choices,
        default= MetalTypeCategory.GOLD,
        )
    type = models.CharField(
        max_length=10,
        choices=TypeCategory.choices,
        default=TypeCategory.TWENTYFOURKARAT,
        verbose_name="किसिम",
    )
    ornament_type = models.CharField(
        max_length=10,
        choices=OrnamentCategory.choices,
        default=OrnamentCategory.STOCK,
        verbose_name="गहनाको किसिम",
    )
    status = models.CharField(
        max_length=10,
        choices=StatusCategory.choices,
        default=StatusCategory.ACTIVE,
        verbose_name="Status",
        help_text="Active, Deleted, or Destroyed"
    )
    maincategory = models.ForeignKey(MainCategory, on_delete=models.CASCADE, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True)
    ornament_name = models.CharField(max_length=255, verbose_name="गहना")
    gross_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Gross Weight (तोल)",
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Metal Weight (तोल)",
    )

    diamond_weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Diamond Weight (हिरा / पत्थर तौल)",
    )
    diamond_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Diamond Rate (per gram)",
        help_text="Rate used for diamond valuation",
    )
    zircon_weight=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Zircon Weight",
        blank=True,
        null=True
    )
    stone_weight=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Stone Weight (पत्थर तौल)",
    )
    stone_percaratprice=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Stone Price",
    )
    
    stone_totalprice=models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Stone Price",
    )
    jarti = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
    )
    jyala= models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
    )
    kaligar = models.ForeignKey(Kaligar, on_delete=models.CASCADE, related_name="ornaments")
    description = models.TextField(blank=True, null=True)
    image=CloudinaryField('image',folder='ornaments/', blank=True, null=True)
    barcode_image = CloudinaryField('Barcode Image', folder='barcodes/', blank=True, null=True)
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ornaments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code or 'NEW'} - {self.ornament_name}"

    def get_purity_factor(self):
        return {
            self.TypeCategory.TWENTYFOURKARAT: Decimal('1.00'),
            self.TypeCategory.TWENTHREEKARAT: Decimal('0.9583'),
            self.TypeCategory.TWENTYTWOKARAT: Decimal('0.92'),
            self.TypeCategory.EIGHTEENKARAT: Decimal('0.75'),
            self.TypeCategory.FOURTEENKARAT: Decimal('0.60'),
        }.get(self.type, Decimal('1.00'))

    @property
    def net_metal_weight(self):
        stored_weight = self.weight or Decimal('0.000')
        if stored_weight > 0:
            return stored_weight

        gross_weight = self.gross_weight or Decimal('0.000')
        diamond_weight = self.diamond_weight or Decimal('0.000')
        stone_weight = self.stone_weight or Decimal('0.000')
        calculated_weight = gross_weight - diamond_weight - stone_weight
        return calculated_weight if calculated_weight > 0 else Decimal('0.000')

    @property
    def net_metal_weight_24k_equivalent(self):
        return self.net_metal_weight * self.get_purity_factor()

    @property
    def gold_net_weight(self):
        if self.metal_type in {self.MetalTypeCategory.GOLD, self.MetalTypeCategory.DIAMOND}:
            return self.net_metal_weight
        return Decimal('0.000')

    @property
    def silver_net_weight(self):
        if self.metal_type == self.MetalTypeCategory.SILVER:
            return self.net_metal_weight
        return Decimal('0.000')
    
    def generate_barcode_image(self):
        """Generate and save barcode image for this ornament."""
        import barcode
        from io import BytesIO
        from django.core.files.base import ContentFile
        import cloudinary.uploader
        import tempfile
        import os
        
        if not self.barcode:
            return
        
        try:
            # Use CODE128 barcode format (most common for products)
            barcode_class = barcode.get_barcode_class('code128')
            barcode_instance = barcode_class(self.barcode, writer=barcode.writer.ImageWriter())
            
            # Generate barcode image to BytesIO
            buffer = BytesIO()
            barcode_instance.write(buffer)
            buffer.seek(0)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp.write(buffer.getvalue())
                tmp_path = tmp.name
            
            try:
                # Upload to Cloudinary
                result = cloudinary.uploader.upload(
                    tmp_path,
                    folder='barcodes/',
                    public_id=f"barcode_{self.barcode}",
                    overwrite=True
                )
                
                # Set the barcode_image to the Cloudinary public_id
                self.barcode_image = result['public_id']
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
        except Exception as e:
            print(f"Error generating barcode image: {e}")
            raise
    
    class Meta:
        ordering = ["id"]
    # Code generation for `code` moved to `ornament.signals.generate_ornament_code`
    # to keep model `save()` simple and avoid coupling persistence logic.