import json

from django.test import TestCase

from order.forms import OrderForm


class OrderFormPaymentLinesTest(TestCase):
    """Verify payment_lines_json is accepted and parsed by OrderForm."""

    def _base_post_data(self):
        return {
            'customer_name': 'Test Customer',
            'phone_number': '9841234567',
            'status': 'order',
            'order_type': 'custom',
            'description': 'Test order',
            'amount': '1000',
            'taxable_amount': '1000',
            'subtotal': '1000',
            'discount': '0',
            'tax': '0',
            'total': '1000',
            'order_lines_json': '[]',
        }

    def test_payment_lines_json_parses_when_valid(self):
        payment_lines = json.dumps([
            {'payment_mode': 'cash', 'amount': 1000, 'debtor_data': None},
        ])
        post_data = self._base_post_data()
        post_data['payment_lines_json'] = payment_lines

        form = OrderForm(post_data)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            json.loads(form.cleaned_data['payment_lines_json']),
            [{'payment_mode': 'cash', 'amount': 1000, 'debtor_data': None}],
        )

    def test_taxable_amount_required_in_form_submission(self):
        post_data = self._base_post_data()
        del post_data['taxable_amount']

        form = OrderForm(post_data)

        self.assertFalse(form.is_valid())
        self.assertIn('taxable_amount', form.errors)
