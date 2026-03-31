from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ornament


def _first_char(value, default='X'):
    """Return first uppercase character for non-empty strings, else default."""
    text = str(value or '').strip()
    return text[0].upper() if text else default


@receiver(post_save, sender=Ornament)
def generate_ornament_code(sender, instance, created, **kwargs):
    """Generate ornament.code and barcode after initial save (so `pk` is available).

    This mirrors the previous `save()` logic: use first letters from
    `ornament_name`, `subcategory`, `maincategory`, `kaligar`, and `ornament_type`
    plus the `pk` to form a readable unique code.
    
    Also generates a unique barcode in format: ORN-{zero_padded_id}
    """
    # Only set code and barcode for newly created objects that don't already have them
    if not created:
        return

    should_update = False
    update_fields = []

    # Generate code if not already set
    if not instance.code:
        name_letter = _first_char(instance.ornament_name)
        sub_category = _first_char(instance.subcategory.name if instance.subcategory else '')
        main_category = _first_char(instance.maincategory.name if instance.maincategory else '')
        kaligar_letter = _first_char(instance.kaligar.name if instance.kaligar else '')
        ornament_type_letter = _first_char(instance.ornament_type)

        instance.code = f"{name_letter}{sub_category}{main_category}{kaligar_letter}{ornament_type_letter}{instance.pk}"
        should_update = True
        update_fields.append('code')

    # Generate barcode if not already set
    if not instance.barcode:
        # Format: ORN-{10-digit zero-padded ID}
        instance.barcode = f"ORN-{instance.pk:010d}"
        should_update = True
        update_fields.append('barcode')

    # Save only the fields that were updated
    if should_update:
        instance.save(update_fields=update_fields)


@receiver(post_save, sender=Ornament)
def generate_barcode_image(sender, instance, created, **kwargs):
    """Generate barcode image after save (ensure barcode is set first)."""
    if instance.barcode and not instance.barcode_image:
        try:
            instance.generate_barcode_image()
            instance.save(update_fields=['barcode_image'])
        except Exception as e:
            print(f"Error generating barcode image for ornament {instance.pk}: {e}")


