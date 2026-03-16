# Customer Purchase - Raw Metal Stock Addition

## Overview
When a customer purchase is marked as **"Refined - Yes"**, the system now automatically adds metal to BOTH the refined and raw metal stock pools.

## Changes Made

### Modified File: `goldsilverpurchase/signals.py`

#### Function: `add_refined_weight_to_metal_stock` (Post-Save Signal)

**Previous Behavior:**
- Only added refined weight to REFINED metal stock (always with 24K purity)

**New Behavior:**
When `refined_status='yes'` and `refined_weight > 0`:

1. **REFINED Stock Entry**
   - Metal Type: Customer's selected metal type
   - Stock Type: REFINED
   - Purity: **24K** (hardcoded)
   - Quantity: refined_weight
   - Location: CUSTOMER_PURCHASE
   - Movement Type: IN

2. **RAW Stock Entry** ✨ NEW
   - Metal Type: Customer's selected metal type
   - Stock Type: RAW
   - Purity: **Customer's selected purity** (22K, 18K, 14K, etc.)
   - Quantity: refined_weight
   - Location: CUSTOMER_PURCHASE
   - Movement Type: IN

#### Function: `remove_refined_weight_from_metal_stock` (Post-Delete Signal)

**Updated to handle:**
- Removal of both refined and raw stock movements when a customer purchase is deleted
- Uses updated reference_id format: `{instance.pk}-refined` and `{instance.pk}-raw`

## Key Features

✅ **Automatic Processing**: No manual intervention needed - triggered automatically on save
✅ **Dual Stock Tracking**: Updates both refined and raw stock simultaneously
✅ **Purity Preservation**: Raw stock retains the customer's selected purity
✅ **Reference ID**: Uses format `{purchase_id}-refined` and `{purchase_id}-raw` for tracking
✅ **Rollback Support**: Deletion of customer purchase removes both movements

## Example Workflow

### Scenario: Customer Purchase Creation
```
Customer brings ornament:
- Metal Type: Gold
- Purity: 22K (customer selected)
- Weight: 10g
- Refined Status: YES
- Refined Weight: 9.5g

System automatically creates:
1. REFINED STOCK:
   - Metal: Gold, Stock Type: Refined, Purity: 24K, Qty: 9.5g

2. RAW STOCK:
   - Metal: Gold, Stock Type: Raw, Purity: 22K, Qty: 9.5g
```

## Database Movements

### MetalStockMovement Entries
- Reference ID Format: `{purchase_id}-refined` (e.g., `1-refined`)
- Reference ID Format: `{purchase_id}-raw` (e.g., `1-raw`)
- Both movements track the same refined_weight quantity
- Location: CUSTOMER_PURCHASE

## Testing

### To Test This Feature:

1. **Create a Customer Purchase:**
   - Go to Customer Purchase form
   - Set `Refined = YES`
   - Select Purity (e.g., 22K, 18K)
   - Set Refined Weight (e.g., 9.5g)
   - Save

2. **Verify Metal Stock Updates:**
   ```sql
   -- Check REFINED stock
   SELECT * FROM goldsilverpurchase_metalstock 
   WHERE metal_type='gold' 
   AND stock_type='refined' 
   AND purity='24K';

   -- Check RAW stock with customer's purity
   SELECT * FROM goldsilverpurchase_metalstock 
   WHERE metal_type='gold' 
   AND stock_type='raw' 
   AND purity='22K';
   ```

3. **Verify MetalStockMovement:**
   ```sql
   SELECT * FROM goldsilverpurchase_metalstockmovement
   WHERE reference_type='CustomerPurchase'
   ORDER BY reference_id DESC;
   ```

## Rollback/Cleanup

If you need to revert to the old behavior:
- Revert the changes in `goldsilverpurchase/signals.py`
- The raw stock entries will no longer be created
- Existing entries will remain in the database

## Error Handling

The signal includes comprehensive error handling:
- Catches exceptions gracefully
- Prints detailed error messages with traceback
- Continues execution if one stock type fails
- Silent failure for non-existent stock types on deletion

## Rate Unit & Cost Tracking

Both refined and raw stock movements inherit:
- **Rate**: Customer purchase rate
- **Rate Unit**: Customer purchase rate_unit (gram, 10gram, tola)
- **Movement Date**: Customer purchase date (or creation date if no purchase date)
- **Notes**: Format: `{customer_name}-{ornament_name}`

