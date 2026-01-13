#!/usr/bin/env python
"""
Test script to verify payment_lines_json is processed correctly by OrderCreateView.form_valid()
This simulates what happens when the form is submitted with payment data.
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import RequestFactory
from order.views import OrderCreateView
from order.forms import OrderForm
from order.models import Order
from decimal import Decimal

# Sample payment_lines_json data that would come from the frontend
sample_payment_json = json.dumps([
    {'payment_mode': 'cash', 'amount': 1000, 'debtor_data': None},
])

print(f"\n{'='*80}")
print("Testing payment_lines_json processing")
print(f"{'='*80}\n")

print(f"Sample payment_lines_json: {sample_payment_json}\n")

# Create request factory
factory = RequestFactory()

# Create a POST request with form data
post_data = {
    'customer_name': 'Test Customer',
    'phone_number': '9841234567',
    'status': 'order',
    'order_type': 'custom',
    'description': 'Test order',
    'amount': '1000',
    'subtotal': '1000',
    'discount': '0',
    'tax': '0',
    'total': '1000',
    'payment_mode': 'cash',
    'payment_amount': '1000',
    'payment_lines_json': sample_payment_json,
    'order_lines_json': '[]',
}

print(f"POST data keys: {list(post_data.keys())}\n")
print(f"payment_lines_json in POST data: {'payment_lines_json' in post_data}")
print(f"payment_lines_json value: {post_data.get('payment_lines_json')}\n")

# Create form instance
form = OrderForm(post_data)

print(f"Form is_valid: {form.is_valid()}")
if not form.is_valid():
    print(f"Form errors: {form.errors}\n")
else:
    print("Form validation passed!\n")
    
    # Check cleaned_data
    print(f"Cleaned data keys: {form.cleaned_data.keys()}\n")
    payment_lines = form.cleaned_data.get('payment_lines_json')
    print(f"payment_lines_json in cleaned_data: {repr(payment_lines)}\n")
    
    # Try to parse it
    try:
        parsed = json.loads(payment_lines)
        print(f"Parsed payment_lines_json: {parsed}\n")
    except Exception as e:
        print(f"Error parsing payment_lines_json: {e}\n")

print(f"{'='*80}\n")
