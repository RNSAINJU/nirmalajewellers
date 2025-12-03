from decimal import Decimal
from django.db import models
from nepali_datetime_field.models import NepaliDateField



class Ornament(models.Model):
    """Standalone ornament master used for stock/order tracking."""

    class OrnamentCategory(models.TextChoices):
        STOCK = 'stock', 'Stock'
        ORDER = 'order', 'Order'

    class TypeCategory(models.TextChoices):
        TWENTYFOURKARAT = '24KARAT', '24 Karat'
        TWENTYTWOKARAT = '22KARAT', '22 Karat'
        EIGHTEENKARAT = '18KARAT', '18 Karat'
        FOURTEENKARAT = '14KARAT', '14 Karat'

    ornament_date = NepaliDateField(null=True, blank=True)
    code = models.CharField(max_length=50, verbose_name="Code / नं.", null=True, blank=True, unique=True)
    ornament_name = models.CharField(max_length=255, verbose_name="गहना")

    type = models.CharField(
        max_length=10,
        choices=TypeCategory.choices,
        default=TypeCategory.TWENTYFOURKARAT,
        verbose_name="किसिम",
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
        verbose_name=" Diamond Weight (हिरा / पत्थर तौल)",
    )

    jarti = models.CharField(max_length=50, blank=True, verbose_name="जर्ती")
    kaligar = models.CharField(max_length=100, blank=True, verbose_name="कसियार")

    ornament_type = models.CharField(
        max_length=10,
        choices=OrnamentCategory.choices,
        default=OrnamentCategory.STOCK,
        verbose_name="गहनाको किसिम",
    )

    customer_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ग्राहकको नाम",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.ornament_name}"

    def save(self, *args, **kwargs):
        # Generate code only for create or when required fields have changed
        is_new = self._state.adding or self.pk is None

        super_save = super().save

            # We defer code generation until after first save (so instance gets an id)
        if is_new:
            # Temporarily set code to empty to avoid unique constraint error
            self.code = ""
            super_save(*args, **kwargs)
            pk_str = str(self.pk)
            name_letter = (self.ornament_name[0].upper() if self.ornament_name else "")
            weight_str = f"{self.weight:.3f}" if self.weight is not None else "0.000"
            weight_digits = weight_str.replace(".", "")[:2]  # first two significant digits (ignoring dot)
            if len(weight_digits) < 2:
                weight_digits = weight_digits.ljust(2, "0")
            kaligar_letter = (self.kaligar[0].upper() if self.kaligar else "")
            ornament_type_letter = (self.ornament_type[0].upper() if self.ornament_type else "")
            customer_letter = (self.customer_name[0].upper() if self.customer_name else "")

            gen_code = f"{pk_str}{name_letter}{weight_digits}{kaligar_letter}{ornament_type_letter}{customer_letter}"
            self.code = gen_code
            # Save again to update the code field
            update_fields = ["code"]
            super().save(update_fields=update_fields)
        else:
            # For update, regenerate if any of the relevant fields have changed
            orig = type(self).objects.filter(pk=self.pk).first()
            code_fields = ['ornament_name', 'weight', 'kaligar', 'ornament_type', 'customer_name']
            should_update = False
            if orig:
                for field in code_fields:
                    if getattr(orig, field) != getattr(self, field):
                        should_update = True
                        break
            if should_update:
                pk_str = str(self.pk)
                name_letter = (self.ornament_name[0].upper() if self.ornament_name else "")
                weight_str = f"{self.weight:.3f}" if self.weight is not None else "0.000"
                weight_digits = weight_str.replace(".", "")[:2]
                if len(weight_digits) < 2:
                    weight_digits = weight_digits.ljust(2, "0")
                kaligar_letter = (self.kaligar[0].upper() if self.kaligar else "")
                ornament_type_letter = (self.ornament_type[0].upper() if self.ornament_type else "")
                customer_letter = (self.customer_name[0].upper() if self.customer_name else "")
                gen_code = f"{pk_str}{name_letter}{weight_digits}{kaligar_letter}{ornament_type_letter}{customer_letter}"
                self.code = gen_code
            super_save(*args, **kwargs)
        return

