from django.db import models

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('fonepay', 'Fonepay'),
        ('bank', 'Bank'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
    ]
    METAL_CHOICES = [
        ('gold', 'Gold'),
        ('silver', 'Silver'),
    ]

    STATUS_CHOICES = [
        ('order', 'Order'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
    ]
    
    sn = models.AutoField(primary_key=True)
    order_date = models.DateField()
    deliver_date = models.DateField()
    customer_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    ornament_name = models.CharField(max_length=255)
    metal_type = models.CharField(max_length=10, choices=METAL_CHOICES)
    ornament_type = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    jarti = models.CharField(max_length=255, blank=True, null=True)
    jyala = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=50, blank=True, null=True)
    stone = models.CharField(max_length=255, blank=True, null=True)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='order')  # New field
    
    

    def __str__(self):
        return f"Order {self.sn} - {self.customer_name}"
