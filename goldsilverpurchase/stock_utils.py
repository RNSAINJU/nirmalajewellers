from decimal import Decimal

from django.db.models import Sum

from .models import MetalStock


def recalculate_metal_stock_quantity(metal_stock):
    """Persist MetalStock.quantity from its movement ledger."""
    if not metal_stock:
        return None

    if not isinstance(metal_stock, MetalStock):
        metal_stock = MetalStock.objects.get(pk=metal_stock)

    totals = {
        row["movement_type"]: row["total"] or Decimal("0.000")
        for row in metal_stock.movements.values("movement_type").annotate(total=Sum("quantity"))
    }
    metal_stock.quantity = (
        totals.get("in", Decimal("0.000"))
        - totals.get("out", Decimal("0.000"))
        + totals.get("adjustment", Decimal("0.000"))
    )
    metal_stock.save()
    return metal_stock
