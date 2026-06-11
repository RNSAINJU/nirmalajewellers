import json

from django.contrib.auth.models import User
from django.test import Client, TestCase

from goldsilverpurchase.models import MetalStock, MetalStockType
from order.forms import MetalStockFormSet
from order.models import Order


class OrderWebFormSubmissionTest(TestCase):
    """Verify order create view persists raw metal lines from the web form."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.client.login(username='testuser', password='testpass123')

        self.raw_stock_type = MetalStockType.objects.create(
            name=MetalStockType.StockTypeChoices.RAW,
            description='Raw metal stock',
        )
        self.metal_stock = MetalStock.objects.create(
            metal_type='gold',
            purity='24K',
            stock_type=self.raw_stock_type,
            quantity=100,
        )

        self.formset_prefix = MetalStockFormSet(instance=None).prefix

    def test_create_order_with_raw_metals(self):
        post_data = {
            'customer_name': 'Test Customer Web',
            'phone_number': '9841234567',
            'status': 'order',
            'order_type': 'custom',
            'description': 'Test order via web form',
            'amount': '1000',
            'taxable_amount': '1000',
            'subtotal': '1000',
            'discount': '0',
            'tax': '0',
            'total': '1000',
            'order_lines_json': '[]',
            'payment_lines_json': json.dumps([
                {'payment_mode': 'cash', 'amount': 0, 'debtor_data': None},
            ]),
            f'{self.formset_prefix}-TOTAL_FORMS': '2',
            f'{self.formset_prefix}-INITIAL_FORMS': '0',
            f'{self.formset_prefix}-MIN_NUM_FORMS': '0',
            f'{self.formset_prefix}-MAX_NUM_FORMS': '1000',
            f'{self.formset_prefix}-0-stock_type': str(self.raw_stock_type.pk),
            f'{self.formset_prefix}-0-metal_type': 'gold',
            f'{self.formset_prefix}-0-purity': '24K',
            f'{self.formset_prefix}-0-quantity': '10',
            f'{self.formset_prefix}-0-rate_unit': 'gram',
            f'{self.formset_prefix}-0-rate_per_gram': '100',
            f'{self.formset_prefix}-0-remarks': 'Test metal entry',
            f'{self.formset_prefix}-0-DELETE': '',
            f'{self.formset_prefix}-1-stock_type': '',
            f'{self.formset_prefix}-1-metal_type': '',
            f'{self.formset_prefix}-1-purity': '',
            f'{self.formset_prefix}-1-quantity': '',
            f'{self.formset_prefix}-1-rate_unit': 'gram',
            f'{self.formset_prefix}-1-rate_per_gram': '',
            f'{self.formset_prefix}-1-remarks': '',
            f'{self.formset_prefix}-1-DELETE': '',
        }

        response = self.client.post('/order/create/', post_data, follow=True)

        self.assertEqual(response.status_code, 200)
        order = Order.objects.filter(customer_name='Test Customer Web').first()
        self.assertIsNotNone(order)

        metals = order.order_metals.all()
        self.assertEqual(metals.count(), 1)
        metal = metals.first()
        self.assertEqual(metal.metal_type, 'gold')
        self.assertEqual(metal.purity, '24K')
        self.assertEqual(metal.quantity, 10)
