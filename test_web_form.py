#!/usr/bin/env python
"""
Test script to verify web form submission with metals works correctly.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from order.models import Order, OrderMetalStock
from goldsilverpurchase.models import MetalStock, MetalStockType
from decimal import Decimal

# Create a test user for login
user, _ = User.objects.get_or_create(username='testuser')
user.set_password('testpass123')
user.save()

# First, ensure we have raw metal stock available
try:
    raw_stock_type = MetalStockType.objects.get(name__icontains='Raw')
except MetalStockType.DoesNotExist:
    raw_stock_type = MetalStockType.objects.create(name='Raw')
    print(f"Created metal stock type: {raw_stock_type}")

# Ensure we have gold stock
metal_stock, created = MetalStock.objects.get_or_create(
    metal_type='gold',
    purity='24K',
    stock_type=raw_stock_type,
    defaults={'quantity': 100}
)
if created:
    print(f"Created metal stock: {metal_stock}")
else:
    if metal_stock.quantity < 50:
        metal_stock.quantity = 100
        metal_stock.save()
    print(f"Metal stock exists: {metal_stock.quantity}g available")

# Test with web form using Django client
client = Client()
client.login(username='testuser', password='testpass123')

# Create an order via web form
print("\n=== Testing Web Form Submission ===")
print("Creating order with raw metals via web form...")

post_data = {
    # Order fields
    'customer_name': 'Test Customer Web',
    'customer_phone': '9841234567',
    'order_date_nepali': '2081-09-15',
    'notes': 'Test order via web form',
    
    # Metal formset data (this is what the template should now generate)
    'order_metals-TOTAL_FORMS': '2',
    'order_metals-INITIAL_FORMS': '0',
    'order_metals-MIN_NUM_FORMS': '0',
    'order_metals-MAX_NUM_FORMS': '1000',
    # Form 0 - Add 10g gold at 100/gram
    'order_metals-0-metal_type': 'gold',
    'order_metals-0-purity': '24K',
    'order_metals-0-quantity': '10',
    'order_metals-0-rate_per_gram': '100',
    'order_metals-0-remarks': 'Test metal entry',
    'order_metals-0-DELETE': '',
    # Form 1 - Empty (ignored)
    'order_metals-1-metal_type': '',
    'order_metals-1-purity': '',
    'order_metals-1-quantity': '',
    'order_metals-1-rate_per_gram': '',
    'order_metals-1-remarks': '',
    'order_metals-1-DELETE': '',
    
    # Ornament lines (empty JSON array)
    'order_lines_json': '[]',
    
    # Payment lines
    'payment_lines_json': '[{"payment_mode":"cash","amount":"0"}]',
}

response = client.post('/order/create/', post_data, follow=True)
print(f"Response status: {response.status_code}")

# Check if order was created
recent_orders = Order.objects.filter(customer_name='Test Customer Web').order_by('-id')
if recent_orders.exists():
    order = recent_orders.first()
    print(f"\n✓ Order created: {order.sn} (ID: {order.id})")
    
    # Check metals
    metals = order.order_metals.all()
    print(f"  Metals in order: {metals.count()}")
    
    if metals.exists():
        print("  ✓ SUCCESS! Metals were created in the order!")
        for metal in metals:
            print(f"    - {metal.metal_type} {metal.purity}: {metal.quantity}g @ {metal.rate_per_gram}/g")
    else:
        print("  ✗ FAILED: No metals found in the order!")
        print("  This means the formset didn't save properly")
else:
    print("✗ Order was not created")

print("\n=== Test Complete ===")
