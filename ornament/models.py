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


class Ornament(models.Model):
    """Ornament master for stock/order tracking."""

    class OrnamentCategory(models.TextChoices):
        STOCK = 'stock', 'Stock'
        ORDER = 'order', 'Order'

    class TypeCategory(models.TextChoices):
        TWENTYFOURKARAT = '24KARAT', '24 Karat'
        TWENTYTWOKARAT = '22KARAT', '22 Karat'
        EIGHTEENKARAT = '18KARAT', '18 Karat'
        FOURTEENKARAT = '14KARAT', '14 Karat'
    
    class MetalTypeCategory(models.TextChoices):
        GOLD = 'Gold', 'Gold'
        SILVER = 'Silver', 'Silver'
        DIAMOND = 'Diamond', 'Diamond'
        OTHERS = 'Others', 'Others'

    ornament_date = NepaliDateField(null=True, blank=True)
    code = models.CharField(max_length=50, verbose_name="Code / नं.", null=True, blank=True, unique=True)
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
    image=CloudinaryField('image',folder='ornaments/', blank=True, null=True)
    order = models.ForeignKey("order.Order", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code or 'NEW'} - {self.ornament_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save first to get PK

        if not self.code:
            name_letter = self.ornament_name[0].upper() if self.ornament_name else 'X'
            sub_category= self.subcategory.name[0].upper() if self.subcategory else 'X'
            main_category= self.maincategory.name[0].upper() if self.maincategory else 'X'
            kaligar_letter = self.kaligar.name[0].upper() if self.kaligar else 'X'
            ornament_type_letter = self.ornament_type[0].upper() if self.ornament_type else 'X'
            self.code = f"{name_letter}{sub_category}{main_category}{kaligar_letter}{ornament_type_letter}{self.pk}"
            super().save(update_fields=['code'])