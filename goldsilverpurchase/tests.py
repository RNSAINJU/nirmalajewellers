
from django.test import TestCase
from .models import CustomerPurchase, MetalStockMovement, MetalStockType, MetalStock
from decimal import Decimal

class CustomerPurchaseRefinedStockMovementTest(TestCase):
	def setUp(self):
		# Create required MetalStockType for refined and raw
		self.refined_type, _ = MetalStockType.objects.get_or_create(
			name=MetalStockType.StockTypeChoices.REFINED,
			defaults={'description': 'Refined metal stock'}
		)
		self.raw_type, _ = MetalStockType.objects.get_or_create(
			name=MetalStockType.StockTypeChoices.RAW,
			defaults={'description': 'Raw metal stock'}
		)

	def test_no_stock_movement_when_not_refined(self):
		"""When refined_status='no', no movements should be created"""
		purchase = CustomerPurchase.objects.create(
			customer_name="Test Customer",
			metal_type="gold",
			ornament_name="Ring",
			weight=Decimal('10.000'),
			refined_status='no',
			refined_weight=None
		)
		# Should have no movements with this reference_id
		refined_movements = MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=f"{purchase.pk}-refined")
		raw_movements = MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=f"{purchase.pk}-raw")
		self.assertFalse(refined_movements.exists())
		self.assertFalse(raw_movements.exists())

	def test_dual_stock_movements_when_refined_and_weight(self):
		"""When refined_status='yes', both refined and raw stock movements should be created"""
		purchase = CustomerPurchase.objects.create(
			customer_name="Test Customer",
			metal_type="gold",
			ornament_name="Ring",
			weight=Decimal('10.000'),
			purity='22K',  # Customer's selected purity
			refined_status='yes',
			refined_weight=Decimal('8.000'),
			rate=Decimal('5000.00'),
			rate_unit='gram'
		)
		
		# Check REFINED movement (with 24K purity)
		refined_movements = MetalStockMovement.objects.filter(
			reference_type='CustomerPurchase', 
			reference_id=f"{purchase.pk}-refined"
		)
		self.assertTrue(refined_movements.exists(), "Refined movement should exist")
		refined_movement = refined_movements.first()
		self.assertEqual(refined_movement.quantity, Decimal('8.000'))
		self.assertEqual(refined_movement.metal_stock.purity, '24K')
		self.assertEqual(refined_movement.metal_stock.stock_type.name, 'refined')
		
		# Check RAW movement (with customer's purity - 22K)
		raw_movements = MetalStockMovement.objects.filter(
			reference_type='CustomerPurchase', 
			reference_id=f"{purchase.pk}-raw"
		)
		self.assertTrue(raw_movements.exists(), "Raw movement should exist")
		raw_movement = raw_movements.first()
		self.assertEqual(raw_movement.quantity, Decimal('8.000'))
		self.assertEqual(raw_movement.metal_stock.purity, '22K')  # Customer's selected purity
		self.assertEqual(raw_movement.metal_stock.stock_type.name, 'raw')

	def test_remove_both_stock_movements_when_status_changed_to_no(self):
		"""When refined_status changes from 'yes' to 'no', both movements should be removed"""
		purchase = CustomerPurchase.objects.create(
			customer_name="Test Customer",
			metal_type="gold",
			ornament_name="Ring",
			weight=Decimal('10.000'),
			purity='22K',
			refined_status='yes',
			refined_weight=Decimal('8.000'),
			rate=Decimal('5000.00'),
			rate_unit='gram'
		)
		# Confirm both movements exist
		self.assertTrue(MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=f"{purchase.pk}-refined").exists())
		self.assertTrue(MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=f"{purchase.pk}-raw").exists())
		
		# Change to not refined
		purchase.refined_status = 'no'
		purchase.save()
		
		# Both movements should now be gone
		self.assertFalse(MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=f"{purchase.pk}-refined").exists())
		self.assertFalse(MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=f"{purchase.pk}-raw").exists())

	def test_no_stock_movement_when_refined_weight_blank(self):
		"""When refined_weight is None, no movements should be created"""
		purchase = CustomerPurchase.objects.create(
			customer_name="Test Customer",
			metal_type="gold",
			ornament_name="Ring",
			weight=Decimal('10.000'),
			purity='22K',
			refined_status='yes',
			refined_weight=None
		)
		refined_movements = MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=f"{purchase.pk}-refined")
		raw_movements = MetalStockMovement.objects.filter(reference_type='CustomerPurchase', reference_id=f"{purchase.pk}-raw")
		self.assertFalse(refined_movements.exists())
		self.assertFalse(raw_movements.exists())

	def test_raw_stock_preserves_customer_purity(self):
		"""Raw stock should preserve the customer's selected purity, not use 24K"""
		test_cases = [
			('22K', 'gold'),
			('18K', 'gold'),
			('14K', 'silver'),
			('24K', 'silver'),
		]
		
		for purity, metal_type in test_cases:
			with self.subTest(purity=purity, metal_type=metal_type):
				purchase = CustomerPurchase.objects.create(
					customer_name=f"Customer {purity}",
					metal_type=metal_type,
					ornament_name="Test Ornament",
					weight=Decimal('10.000'),
					purity=purity,
					refined_status='yes',
					refined_weight=Decimal('8.000'),
					rate=Decimal('5000.00'),
					rate_unit='gram'
				)
				
				raw_movements = MetalStockMovement.objects.filter(
					reference_type='CustomerPurchase', 
					reference_id=f"{purchase.pk}-raw"
				)
				raw_movement = raw_movements.first()
				
				# Raw stock should have the customer's selected purity
				self.assertEqual(raw_movement.metal_stock.purity, purity)
