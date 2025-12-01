from django.db import models
from nepali_datetime_field.models import NepaliDateField

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('fonepay', 'Fonepay'),
        ('bank', 'Bank'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
    ]

    STATUS_CHOICES = [
        ('order', 'Order'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
    ]
    
    sn = models.AutoField(primary_key=True)
    order_date = NepaliDateField(null=True, blank=True)
    deliver_date = NepaliDateField(null=True, blank=True)
    customer_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)

    # Keep order-level fields only; per-item ornament data moved to Ornament model
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='order')

    def __str__(self):
        return f"Order {self.sn} - {self.customer_name}"

# New model to store ornament items linked to an Order
class Ornament(models.Model):
    METAL_CHOICES = [
        ('gold', 'Gold'),
        ('silver', 'Silver'),
    ]

    order = models.ForeignKey(Order, related_name='ornaments', on_delete=models.CASCADE)
    ornament_name = models.CharField(max_length=255)
    metal_type = models.CharField(max_length=10, choices=METAL_CHOICES, default='gold')
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    jarti = models.CharField(max_length=255, blank=True, null=True)
    jyala = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    size = models.CharField(max_length=50, blank=True, null=True)
    stone = models.CharField(max_length=255, blank=True, null=True)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ornament_name} ({self.metal_type})"

