
from django.test import TestCase
from .models import CustomerPurchase, MetalStockMovement, MetalStockType, MetalStock
from decimal import Decimal

class CustomerPurchaseRefinedStockMovementTest(TestCase):
	def setUp(self):
		# Create required MetalStockType for refined
		self.refined_type, _ = MetalStockType.objects.get_or_create(
			name=MetalStockType.StockTypeChoices.REFINED,
			defaults={'description': 'Refined metal stock'}
		)

	def test_no_stock_movement_when_not_refined(self):
		purchase = CustomerPurchase.objects.create(
			customer_name="Test Customer",
			metal_type="gold",
			ornament_name="Ring",
			weight=Decimal('10.000'),
			refined_status='no',
			refined_weight=None
		)
		movement = MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=str(purchase.pk))
		self.assertFalse(movement.exists())

	def test_stock_movement_when_refined_and_weight(self):
		purchase = CustomerPurchase.objects.create(
			customer_name="Test Customer",
			metal_type="gold",
			ornament_name="Ring",
			weight=Decimal('10.000'),
			refined_status='yes',
			refined_weight=Decimal('8.000')
		)
		movement = MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=str(purchase.pk))
		self.assertTrue(movement.exists())
		self.assertEqual(movement.first().quantity, Decimal('8.000'))

	def test_remove_stock_movement_when_status_changed_to_no(self):
		purchase = CustomerPurchase.objects.create(
			customer_name="Test Customer",
			metal_type="gold",
			ornament_name="Ring",
			weight=Decimal('10.000'),
			refined_status='yes',
			refined_weight=Decimal('8.000')
		)
		# Confirm movement exists
		self.assertTrue(MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=str(purchase.pk)).exists())
		# Change to not refined
		purchase.refined_status = 'no'
		purchase.save()
		self.assertFalse(MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=str(purchase.pk)).exists())

	def test_no_stock_movement_when_refined_weight_blank(self):
		purchase = CustomerPurchase.objects.create(
			customer_name="Test Customer",
			metal_type="gold",
			ornament_name="Ring",
			weight=Decimal('10.000'),
			refined_status='yes',
			refined_weight=None
		)
		movement = MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=str(purchase.pk))
		self.assertFalse(movement.exists())
