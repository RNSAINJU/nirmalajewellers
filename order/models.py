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
    ornament = models.ManyToManyField('ornament.Ornament', related_name='orders')
    
    def __str__(self):
        return f"Order {self.sn} - {self.customer_name}"
