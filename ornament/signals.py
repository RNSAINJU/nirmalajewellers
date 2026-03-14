from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ornament


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
        name_letter = instance.ornament_name[0].upper() if instance.ornament_name else 'X'
        sub_category = instance.subcategory.name[0].upper() if instance.subcategory else 'X'
        main_category = instance.maincategory.name[0].upper() if instance.maincategory else 'X'
        kaligar_letter = instance.kaligar.name[0].upper() if instance.kaligar else 'X'
        ornament_type_letter = instance.ornament_type[0].upper() if instance.ornament_type else 'X'

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


