from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ornament


@receiver(post_save, sender=Ornament)
def generate_ornament_code(sender, instance, created, **kwargs):
    """Generate ornament.code after initial save (so `pk` is available).

    This mirrors the previous `save()` logic: use first letters from
    `ornament_name`, `subcategory`, `maincategory`, `kaligar`, and `ornament_type`
    plus the `pk` to form a readable unique code.
    """
    # Only set code for newly created objects that don't already have one
    if not created or instance.code:
        return

    name_letter = instance.ornament_name[0].upper() if instance.ornament_name else 'X'
    sub_category = instance.subcategory.name[0].upper() if instance.subcategory else 'X'
    main_category = instance.maincategory.name[0].upper() if instance.maincategory else 'X'
    kaligar_letter = instance.kaligar.name[0].upper() if instance.kaligar else 'X'
    ornament_type_letter = instance.ornament_type[0].upper() if instance.ornament_type else 'X'

    instance.code = f"{name_letter}{sub_category}{main_category}{kaligar_letter}{ornament_type_letter}{instance.pk}"

    # Save just the code field (second save will not re-enter this branch)
    instance.save(update_fields=['code'])
