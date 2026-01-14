from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import GoldSilverPurchase, MetalStock, MetalStockType


@receiver(post_save, sender=GoldSilverPurchase)
def update_metal_stock_on_purchase(sender, instance, created, **kwargs):
    """
    When a GoldSilverPurchase is created, automatically update the MetalStock
    by adding the purchased quantity to the respective metal type and purity.
    """
    if created:
        # Map metal types from GoldSilverPurchase to MetalStock
        metal_type_map = {
            'gold': MetalStock.MetalType.GOLD,
            'silver': MetalStock.MetalType.SILVER,
            'diamond': 'diamond',  # Diamond not in MetalStock MetalType choices
        }
        
        # Get the metal type for this purchase
        purchase_metal_type = metal_type_map.get(instance.metal_type)
        
        # Skip if metal type is not in MetalStock (e.g., diamond)
        if purchase_metal_type not in [MetalStock.MetalType.GOLD, MetalStock.MetalType.SILVER]:
            return
        
        # Try to get or create a MetalStock record for this metal with matching purity
        try:
            def rate_to_per_gram(rate_value):
                """Normalize rate based on purchase rate_unit."""
                if instance.rate_unit == '10gram':
                    return (rate_value or Decimal('0')) / Decimal('10')
                if instance.rate_unit == 'tola':
                    return (rate_value or Decimal('0')) / Decimal('11.664')
                return rate_value or Decimal('0')

            # Pick stock type based on "raw" keyword in purchase particular
            stock_type = None
            particular_text = (instance.particular or "").lower()
            if "raw" in particular_text:
                stock_type = MetalStockType.objects.filter(name__icontains='raw').first()
            else:
                stock_type = MetalStockType.objects.filter(name__icontains='refined').first()

            # Fallbacks if targeted types are missing
            if not stock_type:
                stock_type = MetalStockType.objects.first()

            if not stock_type:
                # No stock type exists, skip
                return
            
            # Use the purity from the purchase
            purchase_purity = instance.purity or MetalStock.Purity.TWENTYTWOKARAT
            
            # Try to get existing metal stock with same characteristics (metal, stock type, and purity)
            metal_stock, created_stock = MetalStock.objects.get_or_create(
                metal_type=purchase_metal_type,
                stock_type=stock_type,
                purity=purchase_purity,
                location='Purchase',  # Default location for purchased items
                defaults={
                    'quantity': instance.quantity,
                    'rate_unit': instance.rate_unit,
                    'unit_cost': rate_to_per_gram(instance.rate),
                    'total_cost': instance.amount or (instance.quantity * instance.rate),
                }
            )
            
            if not created_stock:
                # Update existing record by adding quantity
                metal_stock.quantity += instance.quantity
                # Update unit cost (weighted average of old and new)
                if metal_stock.quantity > 0:
                    old_total = metal_stock.total_cost or Decimal('0.00')
                    new_total = old_total + (instance.amount or (instance.quantity * rate_to_per_gram(instance.rate)))
                    metal_stock.unit_cost = new_total / metal_stock.quantity
                    metal_stock.total_cost = new_total
                metal_stock.save()
                
        except Exception as e:
            # Log the error but don't fail the purchase creation
            print(f"Error updating MetalStock for purchase {instance.bill_no}: {str(e)}")
