from django.core.management.base import BaseCommand
from decimal import Decimal
from order.models import Order


class Command(BaseCommand):
    help = "Backfill taxable_amount for all existing orders (gold/diamond only, discount proportionally deducted)."

    def handle(self, *args, **options):
        orders = Order.objects.prefetch_related(
            "order_ornaments__ornament", "order_metals"
        ).all()

        updated = 0
        errors = 0

        for order in orders:
            try:
                _D = Decimal

                taxable_ornament_sum = sum(
                    (line.line_amount or _D("0"))
                    for line in order.order_ornaments.all()
                    if line.ornament.metal_type.lower() in ("gold", "diamond")
                )
                taxable_metal_sum = sum(
                    (line.line_amount or _D("0"))
                    for line in order.order_metals.all()
                    if (line.metal_type or "").lower() in ("gold", "diamond")
                )
                taxable_before_discount = taxable_ornament_sum + taxable_metal_sum

                line_sum = (order.amount or _D("0"))
                discount = (order.discount or _D("0"))

                if line_sum:
                    taxable_discount = discount * taxable_before_discount / line_sum
                else:
                    taxable_discount = _D("0")

                taxable_amount = max(_D("0"), taxable_before_discount - taxable_discount)

                Order.objects.filter(pk=order.pk).update(taxable_amount=taxable_amount)
                updated += 1
            except Exception as e:
                self.stderr.write(f"  Error on order {order.pk}: {e}")
                errors += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Updated {updated} orders. Errors: {errors}."
        ))
