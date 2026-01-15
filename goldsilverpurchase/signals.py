from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from decimal import Decimal
from .models import MetalStock, MetalStockType, MetalStockMovement, GoldSilverPurchase

# --- MetalStockMovement for GoldSilverPurchase (always create for 'raw') ---
@receiver(post_save, sender=GoldSilverPurchase)
def create_or_update_metal_stock_and_movement_for_raw(sender, instance, created, **kwargs):
    particular = instance.particular or ''
    if 'raw' not in particular.lower():
        return
    stock_type = MetalStockType.objects.filter(name='raw').first()
    if not stock_type:
        return
    metal_stock, ms_created = MetalStock.objects.get_or_create(
        metal_type=instance.metal_type,
        purity=instance.purity or '24K',
        stock_type=stock_type,
        defaults={
            'quantity': 0,
            'unit_cost': 0,
            'rate_unit': instance.rate_unit or 'tola',
        }
    )
    if not ms_created and not metal_stock.rate_unit:
        metal_stock.rate_unit = instance.rate_unit or 'tola'
        metal_stock.save()
    # Always update or create the movement for this purchase
    MetalStockMovement.objects.update_or_create(
        metal_stock=metal_stock,
        reference_type='GoldSilverPurchase',
        reference_id=instance.bill_no,
        defaults={
            'movement_type': 'in',
            'quantity': instance.quantity,
            'rate': instance.rate,
            'notes': instance.remarks,
            'movement_date': instance.bill_date
        }
    )
    # Immediately recalculate MetalStock
    metal_stock.save()
from .models import GoldSilverPurchase, MetalStock, MetalStockType, CustomerPurchase, MetalStockMovement


# Ensure all signal decorators are defined before use



# Store CustomerPurchase original values to detect changes
_CUSTOMER_PURCHASE_CACHE = {}

# Store GoldSilverPurchase original values to detect changes
_PURCHASE_CACHE = {}


@receiver(pre_save, sender=CustomerPurchase)
def cache_customer_purchase_values(sender, instance, **kwargs):
    """Cache original values before save to detect changes"""
    if instance.pk:
        try:
            old_instance = CustomerPurchase.objects.get(pk=instance.pk)
            _CUSTOMER_PURCHASE_CACHE[instance.pk] = {
                'refined_weight': old_instance.refined_weight,
                'rate': old_instance.rate,
                'rate_unit': old_instance.rate_unit,
                'metal_type': old_instance.metal_type,
            }
        except CustomerPurchase.DoesNotExist:
            pass


@receiver(post_save, sender=CustomerPurchase)
def add_refined_weight_to_metal_stock(sender, instance, created, **kwargs):
    """
    On save: update or create MetalStockMovement for refined stock.
    On edit: update the movement.
    On delete: handled separately.
    """
    try:
        refined_stock_type, _ = MetalStockType.objects.get_or_create(
            name=MetalStockType.StockTypeChoices.REFINED,
            defaults={'description': 'Refined metal stock'}
        )
        metal_stock, _ = MetalStock.objects.get_or_create(
            metal_type=instance.metal_type,
            stock_type=refined_stock_type,
            purity=MetalStock.Purity.TWENTYFOURKARAT,
            defaults={
                'quantity': Decimal('0.000'),
                'unit_cost': Decimal('0.00'),
                'rate_unit': instance.rate_unit,
                'total_cost': Decimal('0.00'),
            }
        )
        if metal_stock.rate_unit != instance.rate_unit:
            metal_stock.rate_unit = instance.rate_unit
            metal_stock.save()
        notes = f"{instance.customer_name or ''}-{instance.ornament_name or ''}"
        movement, _ = MetalStockMovement.objects.update_or_create(
            metal_stock=metal_stock,
            reference_type='CustomerPurchase',
            reference_id=str(instance.pk),
            defaults={
                'movement_type': 'in',
                'quantity': instance.refined_weight,
                'rate': instance.rate,
                'notes': notes,
                'movement_date': instance.purchase_date or instance.created_at,
            }
        )
        # Immediately recalculate MetalStock
        metal_stock.save()
    except Exception as e:
        print(f"[ERROR] Error adding/updating refined weight to MetalStock for customer purchase {getattr(instance, 'sn', instance.pk)}: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_delete, sender=CustomerPurchase)
def remove_refined_weight_from_metal_stock(sender, instance, **kwargs):
    """
    When a CustomerPurchase is deleted, remove the related MetalStockMovement and recalculate MetalStock.
    """
    try:
        refined_stock_type = MetalStockType.objects.get(name=MetalStockType.StockTypeChoices.REFINED)
        metal_stock = MetalStock.objects.get(
            metal_type=instance.metal_type,
            stock_type=refined_stock_type,
            purity=MetalStock.Purity.TWENTYFOURKARAT,
        )
        # Delete the related movement
        MetalStockMovement.objects.filter(
            metal_stock=metal_stock,
            reference_type='CustomerPurchase',
            reference_id=str(instance.pk)
        ).delete()
        # Recalculate MetalStock (unit_cost, total_cost)
        metal_stock.save()
    except Exception as e:
        print(f"[ERROR] Error removing refined weight from MetalStock for customer purchase {getattr(instance, 'sn', instance.pk)}: {str(e)}")
        import traceback
        traceback.print_exc()

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
            TOLA_TO_GRAM = Decimal('11.6643')
            
            def rate_to_per_tola(rate_value, rate_unit):
                """Convert rate to per-tola based on rate_unit."""
                if rate_unit == 'tola':
                    return rate_value or Decimal('0')
                elif rate_unit == '10gram':
                    # per 10gram to per gram, then to per tola
                    per_gram = (rate_value or Decimal('0')) / Decimal('10')
                    return per_gram * TOLA_TO_GRAM
                elif rate_unit == 'gram':
                    # per gram to per tola
                    return (rate_value or Decimal('0')) * TOLA_TO_GRAM
                return Decimal('0')
            
            def rate_to_per_gram(rate_value, rate_unit):
                """Normalize rate to per-gram based on rate_unit."""
                if rate_unit == '10gram':
                    return (rate_value or Decimal('0')) / Decimal('10')
                elif rate_unit == 'tola':
                    return (rate_value or Decimal('0')) / TOLA_TO_GRAM
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
            
            # Convert purchase rate to per-tola
            rate_in_tola = rate_to_per_tola(instance.rate, instance.rate_unit)
            
            # Calculate total cost: quantity in grams × rate converted to per-gram
            rate_per_gram = rate_to_per_gram(instance.rate, instance.rate_unit)
            total_cost_for_stock = instance.quantity * rate_per_gram
            
            # Try to get existing metal stock with same characteristics (metal, stock type, and purity)
            metal_stock, created_stock = MetalStock.objects.get_or_create(
                metal_type=purchase_metal_type,
                stock_type=stock_type,
                purity=purchase_purity,
                location='Purchase',  # Default location for purchased items
                defaults={
                    'quantity': instance.quantity,
                    'rate_unit': 'tola',  # Always store as tola
                    'unit_cost': rate_in_tola,  # Rate converted to per-tola
                    'total_cost': total_cost_for_stock,
                }
            )
            
            if not created_stock:
                # Update existing record by adding quantity
                metal_stock.quantity += instance.quantity
                # Update unit cost (weighted average by quantity)
                if metal_stock.quantity > 0:
                    rate_per_gram_new = rate_to_per_gram(instance.rate, instance.rate_unit)
                    new_purchase_total = instance.quantity * rate_per_gram_new
                    old_total = metal_stock.total_cost or Decimal('0.00')
                    new_total = old_total + new_purchase_total
                    metal_stock.unit_cost = new_total / metal_stock.quantity
                    metal_stock.total_cost = new_total
                    metal_stock.rate_unit = 'tola'  # Ensure it stays as tola
                metal_stock.save()
                
        except Exception as e:
            # Log the error but don't fail the purchase creation
            print(f"Error updating MetalStock for purchase {instance.bill_no}: {str(e)}")


@receiver(pre_save, sender=GoldSilverPurchase)
def store_original_purchase_values(sender, instance, **kwargs):
    """Store original values before update to detect changes."""
    if instance.pk:
        try:
            original = GoldSilverPurchase.objects.get(pk=instance.pk)
            _PURCHASE_CACHE[instance.pk] = {
                'quantity': original.quantity,
                'rate': original.rate,
                'rate_unit': original.rate_unit,
                'metal_type': original.metal_type,
                'purity': original.purity,
                'amount': original.amount,
            }
        except GoldSilverPurchase.DoesNotExist:
            pass


@receiver(post_save, sender=GoldSilverPurchase)
def update_metal_stock_on_purchase_edit(sender, instance, created, **kwargs):
    """
    When a GoldSilverPurchase is updated, adjust the MetalStock accordingly.
    """
    if created:
        return  # Already handled by update_metal_stock_on_purchase
    
    # Handle update case
    original_data = _PURCHASE_CACHE.pop(instance.pk, None)
    if not original_data:
        return
    
    try:
        # Helper functions
        TOLA_TO_GRAM = Decimal('11.6643')
        
        def rate_to_per_tola(rate_value, rate_unit):
            """Convert rate to per-tola based on rate_unit."""
            if rate_unit == 'tola':
                return rate_value or Decimal('0')
            elif rate_unit == '10gram':
                per_gram = (rate_value or Decimal('0')) / Decimal('10')
                return per_gram * TOLA_TO_GRAM
            elif rate_unit == 'gram':
                return (rate_value or Decimal('0')) * TOLA_TO_GRAM
            return Decimal('0')
        
        def rate_to_per_gram(rate_value, rate_unit):
            """Normalize rate based on rate_unit."""
            if rate_unit == '10gram':
                return (rate_value or Decimal('0')) / Decimal('10')
            if rate_unit == 'tola':
                return (rate_value or Decimal('0')) / TOLA_TO_GRAM
            return rate_value or Decimal('0')
        
        metal_type_map = {
            'gold': MetalStock.MetalType.GOLD,
            'silver': MetalStock.MetalType.SILVER,
        }
        
        old_metal_type = metal_type_map.get(original_data['metal_type'])
        new_metal_type = metal_type_map.get(instance.metal_type)
        
        # Skip if metal type not in MetalStock
        if new_metal_type not in [MetalStock.MetalType.GOLD, MetalStock.MetalType.SILVER]:
            return
        
        # Determine stock type
        particular_text = (instance.particular or "").lower()
        stock_type = None
        if "raw" in particular_text:
            stock_type = MetalStockType.objects.filter(name__icontains='raw').first()
        else:
            stock_type = MetalStockType.objects.filter(name__icontains='refined').first()
        
        if not stock_type:
            stock_type = MetalStockType.objects.first()
        if not stock_type:
            return
        
        # If metal type or purity changed, need to handle old and new stocks
        if old_metal_type != new_metal_type or original_data['purity'] != instance.purity:
            # Remove from old metal stock
            try:
                old_stock = MetalStock.objects.get(
                    metal_type=old_metal_type,
                    purity=original_data['purity']
                )
                old_stock.quantity -= original_data['quantity']
                if old_stock.quantity <= 0:
                    old_stock.delete()
                else:
                    old_stock.save()
            except MetalStock.DoesNotExist:
                pass
            
            # Add to new metal stock
            rate_in_tola = rate_to_per_tola(instance.rate, instance.rate_unit)
            metal_stock, _ = MetalStock.objects.get_or_create(
                metal_type=new_metal_type,
                stock_type=stock_type,
                purity=instance.purity,
                location='Purchase',
                defaults={
                    'quantity': instance.quantity,
                    'rate_unit': 'tola',  # Always store as tola
                    'unit_cost': rate_in_tola,  # Rate converted to per-tola
                }
            )
            metal_stock.quantity += instance.quantity
            metal_stock.rate_unit = 'tola'  # Ensure it's tola
            metal_stock.save()
        else:
            # Same metal and purity, adjust quantity and cost
            quantity_diff = instance.quantity - original_data['quantity']
            
            metal_stock = MetalStock.objects.filter(
                metal_type=new_metal_type,
                purity=instance.purity
            ).first()
            
            if metal_stock:
                # Recalculate total cost properly
                old_purchase_rate_per_gram = rate_to_per_gram(original_data['rate'], original_data['rate_unit'])
                old_purchase_total = original_data['quantity'] * old_purchase_rate_per_gram
                
                new_purchase_rate_per_gram = rate_to_per_gram(instance.rate, instance.rate_unit)
                new_purchase_total = instance.quantity * new_purchase_rate_per_gram
                
                old_total = metal_stock.total_cost or Decimal('0.00')
                # Remove old purchase contribution, add new purchase contribution
                intermediate_total = old_total - old_purchase_total
                new_total = intermediate_total + new_purchase_total
                
                metal_stock.quantity += quantity_diff
                metal_stock.rate_unit = 'tola'  # Ensure it's tola
                
                if metal_stock.quantity > 0:
                    metal_stock.unit_cost = new_total / metal_stock.quantity
                    metal_stock.total_cost = new_total
                else:
                    metal_stock.unit_cost = Decimal('0.00')
                    metal_stock.total_cost = Decimal('0.00')
                
                if metal_stock.quantity <= 0:
                    metal_stock.delete()
                else:
                    metal_stock.save()
    
    except Exception as e:
        print(f"Error updating MetalStock on edit for purchase {instance.bill_no}: {str(e)}")


@receiver(post_delete, sender=GoldSilverPurchase)
def update_metal_stock_on_purchase_delete(sender, instance, **kwargs):
    """
    When a GoldSilverPurchase is deleted, reduce the MetalStock accordingly.
    """
    try:
        metal_type_map = {
            'gold': MetalStock.MetalType.GOLD,
            'silver': MetalStock.MetalType.SILVER,
        }
        
        purchase_metal_type = metal_type_map.get(instance.metal_type)
        
        # Skip if not gold or silver
        if purchase_metal_type not in [MetalStock.MetalType.GOLD, MetalStock.MetalType.SILVER]:
            return
        
        # Find and update the metal stock
        metal_stock = MetalStock.objects.filter(
            metal_type=purchase_metal_type,
            purity=instance.purity
        ).first()
        
        if metal_stock:
            metal_stock.quantity -= instance.quantity
            
            if metal_stock.quantity <= 0:
                # Delete if no quantity left
                metal_stock.delete()
            else:
                # Adjust total cost proportionally
                if metal_stock.quantity > 0:
                    # Recalculate by removing the deleted purchase's contribution
                    old_total = metal_stock.total_cost or Decimal('0.00')
                    purchase_total = instance.amount or (instance.quantity * instance.rate)
                    new_total = max(Decimal('0.00'), old_total - purchase_total)
                    metal_stock.unit_cost = new_total / metal_stock.quantity if metal_stock.quantity > 0 else Decimal('0.00')
                    metal_stock.total_cost = new_total
                
                metal_stock.save()
    
    except Exception as e:
        print(f"Error updating MetalStock on delete for purchase {instance.bill_no}: {str(e)}")



