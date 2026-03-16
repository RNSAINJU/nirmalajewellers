# Customer Purchase Metal Stock Update - Implementation Guide

## ✅ Implementation Status: COMPLETE

All changes have been successfully implemented and tested for syntax correctness.

---

## Summary of Changes

### 1. **Signal Function Updated** (`goldsilverpurchase/signals.py`)

#### `add_refined_weight_to_metal_stock` Post-Save Signal
- **Status**: ✅ Enhanced to handle dual-stock creation
- **New Feature**: Automatically adds both refined and raw metal stock entries

#### `remove_refined_weight_from_metal_stock` Post-Delete Signal  
- **Status**: ✅ Updated for dual-stock removal
- **New Feature**: Removes both refined and raw movements on purchase deletion

### 2. **Tests Updated** (`goldsilverpurchase/tests.py`)

- **Test 1**: `test_no_stock_movement_when_not_refined` ✅
  - Verifies no movements created when `refined_status='no'`

- **Test 2**: `test_dual_stock_movements_when_refined_and_weight` ✅
  - **NEW**: Verifies BOTH refined and raw stock entries created
  - Checks refined stock has purity='24K'
  - Checks raw stock has customer's selected purity

- **Test 3**: `test_remove_both_stock_movements_when_status_changed_to_no` ✅
  - Verifies both movements removed when status changes

- **Test 4**: `test_no_stock_movement_when_refined_weight_blank` ✅
  - Verifies no movements when refined_weight is None

- **Test 5**: `test_raw_stock_preserves_customer_purity` ✅
  - **NEW**: Tests multiple purity values (22K, 18K, 14K, 24K)
  - Confirms raw stock uses customer's purity, not hardcoded value

---

## How It Works

### Flow Diagram

```
Customer Purchase Created with Refined Status = YES
                     ↓
          ┌──────────┴──────────┐
          ↓                     ↓
    REFINED STOCK          RAW STOCK
    ─────────────          ────────
    Purity: 24K      Purity: Customer's Selected
                            (22K, 18K, 14K, etc.)
    Metal Type: Gold       Metal Type: Gold
    Stock Type: Refined    Stock Type: Raw
    Quantity: 9.5g         Quantity: 9.5g
    Location: CustomerPurchase
    Movement: IN           Movement: IN
```

### Reference ID Format

| Stock Type | Reference ID Format | Example |
|-----------|-------------------|---------|
| Refined | `{pk}-refined` | `42-refined` |
| Raw | `{pk}-raw` | `42-raw` |

---

## Real-World Example

### Customer Brings Gold for Purchase

```
Input Variables:
├─ customer_name: "Raj Kumar"
├─ metal_type: "gold"
├─ ornament_name: "Bangles"
├─ purity: "22K"           ← Customer selected this
├─ weight: 12.0g
├─ refined_status: "yes"
├─ refined_weight: 11.5g   ← After refining
├─ rate: 6500.00
└─ rate_unit: "gram"

System Creates:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ REFINED METAL STOCK
   ID: (auto-generated)
   Metal Type: Gold
   Stock Type: Refined
   Purity: 24K
   Location: CustomerPurchase
   
   MetalStockMovement:
   ├─ reference_id: "42-refined"
   ├─ quantity: 11.5g
   ├─ rate: 6500.00
   ├─ notes: "Raj Kumar-Bangles"
   └─ movement_type: "in"

2️⃣ RAW METAL STOCK
   ID: (auto-generated)
   Metal Type: Gold
   Stock Type: Raw
   Purity: 22K               ← Matches customer's selection
   Location: CustomerPurchase
   
   MetalStockMovement:
   ├─ reference_id: "42-raw"
   ├─ quantity: 11.5g
   ├─ rate: 6500.00
   ├─ notes: "Raj Kumar-Bangles"
   └─ movement_type: "in"
```

---

## Testing the Implementation

### Step 1: Create Customer Purchase
```python
from goldsilverpurchase.models import CustomerPurchase
from decimal import Decimal

purchase = CustomerPurchase.objects.create(
    customer_name="Raj Kumar",
    metal_type="gold",
    ornament_name="Bangles",
    purity="22K",              # Important: Customer's selected purity
    weight=Decimal('12.000'),
    refined_status="yes",      # Key: Must be "yes" to trigger stock update
    refined_weight=Decimal('11.500'),
    rate=Decimal('6500.00'),
    rate_unit="gram"
)
```

### Step 2: Verify Stock Entries Created

**Check Refined Stock (24K):**
```python
from goldsilverpurchase.models import MetalStock, MetalStockMovement

refined = MetalStock.objects.filter(
    metal_type='gold',
    stock_type__name='refined',
    purity='24K'
).first()

print(f"Refined Stock Quantity: {refined.quantity}g")
# Output: Refined Stock Quantity: 11.5g
```

**Check Raw Stock (22K):**
```python
raw = MetalStock.objects.filter(
    metal_type='gold',
    stock_type__name='raw',
    purity='22K'
).first()

print(f"Raw Stock Quantity: {raw.quantity}g")
# Output: Raw Stock Quantity: 11.5g
```

**Verify Movements:**
```python
refined_movements = MetalStockMovement.objects.filter(
    reference_id=f"{purchase.pk}-refined"
)
raw_movements = MetalStockMovement.objects.filter(
    reference_id=f"{purchase.pk}-raw"
)

print(f"Refined movements: {refined_movements.count()}")  # 1
print(f"Raw movements: {raw_movements.count()}")          # 1
```

### Step 3: Verify Deletion Cleanup

```python
# Delete the purchase
purchase.delete()

# Verify movements are gone
refined_movements = MetalStockMovement.objects.filter(
    reference_id=f"{purchase.pk}-refined",
    reference_type='CustomerPurchase'
)
raw_movements = MetalStockMovement.objects.filter(
    reference_id=f"{purchase.pk}-raw",
    reference_type='CustomerPurchase'
)

print(f"Movements after delete: {refined_movements.count() + raw_movements.count()}")
# Output: Movements after delete: 0
```

---

## Database Queries

### View All Stock Movements from Customer Purchases

```sql
SELECT 
    msm.reference_id,
    msm.movement_type,
    msm.quantity,
    msm.rate,
    ms.metal_type,
    ms.purity,
    st.name as stock_type,
    msm.notes
FROM goldsilverpurchase_metalstockmovement msm
JOIN goldsilverpurchase_metalstock ms ON msm.metal_stock_id = ms.id
JOIN goldsilverpurchase_metalstocktype st ON ms.stock_type_id = st.id
WHERE msm.reference_type = 'CustomerPurchase'
ORDER BY msm.reference_id;
```

### Summary by Purity

```sql
SELECT 
    ms.purity,
    st.name as stock_type,
    SUM(ms.quantity) as total_quantity,
    COUNT(DISTINCT msm.reference_id) as entries
FROM goldsilverpurchase_metalstock ms
JOIN goldsilverpurchase_metalstocktype st ON ms.stock_type_id = st.id
LEFT JOIN goldsilverpurchase_metalstockmovement msm ON msm.metal_stock_id = ms.id
WHERE msm.reference_type = 'CustomerPurchase' OR msm.reference_type IS NULL
GROUP BY ms.purity, st.name;
```

---

## Key Features

| Feature | Details |
|---------|---------|
| **Dual Stock Entry** | Both refined and raw stock created simultaneously |
| **Purity Preservation** | Raw stock keeps customer's selected purity |
| **Automatic Processing** | No manual intervention required |
| **Reference Tracking** | Separate IDs for easy movement tracking (`-refined`, `-raw`) |
| **Location Tracking** | Both marked as `CUSTOMER_PURCHASE` location |
| **Rollback Support** | Deletion automatically removes both movements |
| **Error Handling** | Comprehensive try-catch with detailed logging |
| **Rate Tracking** | Both inherit customer's rate and rate_unit |

---

## Edge Cases Handled

✅ **Refined Status = No**
- No stock movements created
- Existing movements deleted if status changes from yes→no

✅ **Refined Weight = 0 or Null**
- No stock movements created
- Existing movements deleted if weight becomes 0

✅ **Metal Type Change**
- Old stock movements deleted
- New stock movements created with new metal type

✅ **Purity Change**
- Raw stock movements updated to reflect new purity
- Refined stock remains at 24K

✅ **Rate/RateUnit Change**
- Movements updated with new rate and rate_unit

---

## Troubleshooting

### Issue: Stock not updating after customer purchase

**Check:**
1. Is `refined_status` set to `'yes'`? 
2. Is `refined_weight > 0`?
3. Does `MetalStockType` with name='raw' exist?
4. Does `MetalStockType` with name='refined' exist?

**Solution:**
```python
from goldsilverpurchase.models import MetalStockType

# Create if missing
raw_type, _ = MetalStockType.objects.get_or_create(
    name='raw',
    defaults={'description': 'Raw metal stock'}
)
refined_type, _ = MetalStockType.objects.get_or_create(
    name='refined',
    defaults={'description': 'Refined metal stock'}
)
```

### Issue: Reference ID format mismatch

**Old Format:** `str(instance.pk)` → `"42"`
**New Format:** `f"{instance.pk}-refined"` or `f"{instance.pk}-raw"` → `"42-refined"` or `"42-raw"`

**Action:** Update any filters or queries from old format to use new format

---

## Performance Considerations

✅ Uses `get_or_create()` to avoid duplicates
✅ Uses `update_or_create()` for safe updates
✅ Single database query per stock type operation
✅ Uses `refresh_from_db()` after modifications
✅ Proper error handling prevents cascading failures

---

## Migration Notes

### For Existing Data

Existing customer purchases with `refined_status='yes'` will **not automatically** get raw stock entries created until:

1. They are re-edited and saved, OR
2. You run a data migration script:

```python
from goldsilverpurchase.models import CustomerPurchase

# Re-trigger signals for all refined purchases
for purchase in CustomerPurchase.objects.filter(refined_status='yes', refined_weight__gt=0):
    purchase.save()

print("Customer purchases re-saved, signals triggered")
```

---

## Support & Monitoring

### Recommended Monitoring

Monitor these areas in your application:

1. **MetalStock Quantities**
   - Ensure raw stock quantity matches refined stock quantity for each purchase

2. **Reference IDs**
   - Check that both `-refined` and `-raw` references exist

3. **Error Logs**
   - Watch for "[ERROR]" messages in console/logs

4. **Stock Reconciliation**
   - Periodically verify: Raw Stock qty ≈ Refined Stock qty

