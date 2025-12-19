from django.db import models
from nepali_datetime_field.models import NepaliDateField

from order.models import Order


class Sale(models.Model):
    """Represents a finalized sale created from an Order.

    Physically lives in the `sales` app, but logically belongs to the
    `order` app (via `app_label`) so existing migrations and the database
    table continue to work unchanged.
    """

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="sale",
    )

    # Date when the sale is recorded (typically deliver_date or today)
    sale_date = NepaliDateField(null=True, blank=True)

    # Optional separate bill number for the sale
    bill_no = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "order"  # keep model under the `order` app for migrations
        db_table = "order_sale"  # reuse existing table name
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ["-sale_date", "-created_at"]

    def __str__(self):
        return f"Sale for Order {self.order_id}"
