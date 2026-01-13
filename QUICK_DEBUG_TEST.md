# Quick Start: Payment Debug Testing

## TL;DR - Do This Now

1. **Open the order creation form**: http://localhost:8000/order/create/
2. **Open Browser DevTools**: Press `F12` → Click "Console" tab
3. **Fill in basic info**: 
   - Customer Name: `Test Customer`
   - Phone: `9841234567`
4. **Add a payment**:
   - Look for "Payment" section (right side of form)
   - Payment Mode: Select `Cash` (already selected)
   - Amount: Enter `1000`
5. **Submit the form**: Click "Save Order"
6. **Capture console output**: 
   - Right-click in console → "Save as..." → Save to file
   - OR copy all visible console text
7. **Watch Django terminal**: Look for lines starting with `[DEBUG` or `[FORM`
   - Copy all output related to payment processing
8. **Report back**: Share both console and terminal outputs

## What to Look For

### In Browser Console - Should see:
```
[FORM SUBMIT] ========== FORM SUBMISSION HANDLER CALLED ==========
[FORM SUBMIT] Found 1 payment rows
[DEBUG] getPaymentRowsData - found 1 payment rows
[DEBUG] Row 0 RAW: modeSelect?.value="cash", amountInput?.value="1000"
[FORM SUBMIT] payment_lines_json value: [{"payment_mode":"cash","amount":1000,"debtor_data":null}]
[FORM SUBMIT] ========== SUBMITTING FORM ==========
```

### In Django Terminal - Should see:
```
[FORM CLEAN] payment_lines_json received: '[{"payment_mode":"cash","amount":1000,"debtor_data":null}]'
[DEBUG ORDER CREATE] ========== PAYMENT PROCESSING START ==========
[DEBUG ORDER CREATE] Processing payment #0: mode=cash, amount=1000
[DEBUG ORDER CREATE] Creating OrderPayment: mode=cash, amount=1000
[DEBUG ORDER CREATE] Total payments created: 1
[DEBUG ORDER CREATE] After recompute: payment_amount=1000.00, payment_mode=cash
```

### Then Check the Order:
After form submits and redirects to order list:
- Click on the newly created order
- In order details, verify:
  - Payment Mode: shows "Cash"  
  - Payment Amount: shows "1000.00" (NOT "0.00")

## If Something's Wrong

### Browser console shows empty/missing lines
- Payment form might not be working correctly in frontend
- Might be JavaScript error preventing recalcPayments() from running

### Django terminal shows `amount=0`
- User didn't enter a payment amount (left it blank)
- OR JavaScript read the blank value instead of the entered value

### Django terminal shows `Total payments created: 0`
- Either frontend sent empty JSON (see #1 above)
- OR backend skipped all payments because amount=0

## Files Modified for Debug
- `order/forms.py` - Added clean() method logging
- `order/templates/order/order_form.html` - Added console.log() everywhere
- `order/views.py` - Added detailed payment processing logs
- `DEBUG_PAYMENT_GUIDE.md` - Full debugging guide (this folder)
- `CHANGES_SUMMARY.md` - What changed and why

## Still Stuck?
1. Check that Django server is running: Should see "Starting development server at http://127.0.0.1:8000/"
2. Make sure you have a fresh page load (press Ctrl+Shift+R to hard refresh)
3. Check browser console before any action - should be empty/clean
4. Try creating a simple order first without any payments, then with payments
