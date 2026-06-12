import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ornament.models import Kaligar, Ornament

from .forms import MetalStockFormSet
from .models import Order, OrderOrnament


class OrderUpdateOrnamentReleaseTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="operator", password="password")
        self.client.force_login(self.user)

    def test_removing_all_ornament_lines_releases_previous_ornaments(self):
        order = Order.objects.create(
            customer_name="Test Customer",
            phone_number="1234567",
            total=Decimal("100.00"),
        )
        kaligar = Kaligar.objects.create(name="Test Kaligar")
        ornament = Ornament.objects.create(
            code="ORN-1",
            ornament_name="Ring",
            kaligar=kaligar,
            order=order,
            ornament_type=Ornament.OrnamentCategory.ORDER,
        )
        OrderOrnament.objects.create(
            order=order,
            ornament=ornament,
            line_amount=Decimal("100.00"),
        )

        formset_prefix = MetalStockFormSet(instance=order).prefix
        response = self.client.post(
            reverse("order:update", args=[order.pk]),
            {
                "customer_name": "Test Customer",
                "phone_number": "1234567",
                "status": "order",
                "order_type": "custom",
                "amount": "0.00",
                "taxable_amount": "0.00",
                "subtotal": "0.00",
                "discount": "0.00",
                "tax": "0.00",
                "total": "0.00",
                "order_lines_json": json.dumps([]),
                "payment_lines_json": json.dumps([]),
                f"{formset_prefix}-TOTAL_FORMS": "0",
                f"{formset_prefix}-INITIAL_FORMS": "0",
                f"{formset_prefix}-MIN_NUM_FORMS": "0",
                f"{formset_prefix}-MAX_NUM_FORMS": "1000",
            },
        )

        self.assertEqual(response.status_code, 302)
        ornament.refresh_from_db()
        self.assertIsNone(ornament.order)
        self.assertEqual(ornament.ornament_type, Ornament.OrnamentCategory.STOCK)
