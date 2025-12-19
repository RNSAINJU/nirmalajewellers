#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from ornament.models import Ornament

total = Ornament.objects.count()
unassigned = Ornament.objects.filter(order__isnull=True).count()

print(f'Total ornaments: {total}')
print(f'Unassigned: {unassigned}')
print('\nFirst 3 unassigned ornaments:')

for o in Ornament.objects.filter(order__isnull=True)[:3]:
    print(f'  ID: {o.id}, Code: {o.code}, Name: {o.ornament_name}, Metal: {o.metal_type}')
