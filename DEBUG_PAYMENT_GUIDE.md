# Payment Data Persistence Debug Guide

## Problem Statement
When creating an order with payment information (e.g., Cash Rs. 1000), the order saves but:
- payment_amount field remains 0
- payment_mode shows "Cash" (default) instead of actual selection  
- No OrderPayment records created in database

## Root Cause Analysis
The system flow for payment persistence:
1. **Frontend (JavaScript)**: User enters payment amount in the form → recalcPayments() collects data → sets hidden field `payment_lines_json`
2. **Form Submission**: POST sends hidden fields to backend
3. **Django Form**: Form.clean() validates and stores `payment_lines_json` in cleaned_data
4. **View (form_valid)**: Reads `payment_lines_json` from cleaned_data → parses JSON → creates OrderPayment objects
5. **Backend (model)**: recompute_totals_from_lines() calculates payment_amount and payment_mode from OrderPayment objects

**Critical Issue Identified**: If payment_lines_json contains entries with amount <= 0, they are skipped, resulting in no OrderPayment objects being created. The order.payment_amount then defaults to 0 and payment_mode defaults to 'cash'.

## Debugging Steps

### Step 1: Browser Console Monitoring
1. Open the order creation form: `/order/create/`
2. Press **F12** to open DevTools
3. Go to **Console** tab
4. Fill in customer details (name, phone)
5. Add a payment row with mode "Cash" and amount (e.g., 1000)
6. Click "Save Order"
7. Watch console for these log patterns:

**Expected output sequence:**
```
[FORM SUBMIT] ========== FORM SUBMISSION HANDLER CALLED ==========
[FORM SUBMIT] Found X payment rows
[FORM SUBMIT] Row 0 BEFORE recalcPayments: mode="cash", amount="1000"
[FORM SUBMIT] About to call recalcPayments()...
[DEBUG] getPaymentRowsData - found 1 payment rows
[DEBUG] Row 0 RAW: modeSelect?.value="cash", amountInput?.value="1000"
[DEBUG] Row 0 PARSED: mode='cash', amountVal=1000
[DEBUG] getPaymentRowsData - FINAL rows array: [{"payment_mode":"cash","amount":1000,"debtor_data":null}]
[DEBUG] recalcPayments - payment rows data: [...]
[DEBUG] Set payment_amount to: 1000.00
[DEBUG] Set payment_mode to: cash
[DEBUG] Set payment_lines_json to: [{"payment_mode":"cash","amount":1000,"debtor_data":null}]
[FORM SUBMIT] payment_lines_json field exists: true
[FORM SUBMIT] payment_lines_json value: [{"payment_mode":"cash","amount":1000,"debtor_data":null}]
[FORM SUBMIT] payment_mode: cash
[FORM SUBMIT] payment_amount: 1000.00
[FORM SUBMIT] ========== SUBMITTING FORM ==========
```

### Step 2: Django Terminal Monitoring
1. Look at terminal where Django server is running
2. After form submission, you should see these logs:

**Expected output sequence:**
```
[FORM CLEAN] payment_lines_json received: '[{"payment_mode":"cash","amount":1000,"debtor_data":null}]'
[FORM CLEAN] type: <class 'str'>, length: 63
[FORM CLEAN] Parsed JSON: [{'payment_mode': 'cash', 'amount': 1000, 'debtor_data': None}]
[DEBUG] form_valid called
[DEBUG] form.cleaned_data keys: dict_keys([...., 'payment_lines_json', ...])
[DEBUG] Order saved with sn=NNN
[DEBUG ORDER CREATE] ========== PAYMENT PROCESSING START ==========
[DEBUG ORDER CREATE] payment_lines_json raw value: '[{"payment_mode":"cash","amount":1000,"debtor_data":null}]'
[DEBUG ORDER CREATE] payment_lines_json length: 63
[DEBUG ORDER CREATE] payments_data after JSON parse: [{'payment_mode': 'cash', 'amount': 1000, 'debtor_data': None}]
[DEBUG ORDER CREATE] Processing payment #0: mode=cash, amount=1000
[DEBUG ORDER CREATE] Creating OrderPayment: mode=cash, amount=1000
[DEBUG ORDER CREATE] OrderPayment created successfully, id=123
[DEBUG ORDER CREATE] ========== PAYMENT PROCESSING END ==========
[DEBUG ORDER CREATE] Total payments created: 1
[DEBUG ORDER CREATE] Total OrderPayment objects for this order: 1
[DEBUG ORDER CREATE] Calling recompute_totals_from_lines()...
[DEBUG ORDER CREATE] After recompute: payment_amount=1000.00, payment_mode=cash
[CREATE VIEW] Order NNN form_valid completed - returning redirect
```

## What to Report
Please collect the following and report back:

1. **Browser Console Output**: Screenshot or copy/paste of entire console output during form submission
2. **Django Terminal Output**: Screenshot or copy/paste of terminal output right after submitting the form
3. **Order Details**: After redirected to order list, click on the created order and check:
   - Does payment_amount show as 0 or the value you entered?
   - Does payment_mode show "Cash" or something else?
   - In Django admin at Order table, what are the values for this order's payment_amount and payment_mode?
   - How many OrderPayment records exist for this order in the database?

## Potential Issues to Watch For

### Issue A: Empty payment_lines_json in terminal output
If you see:
```
[DEBUG ORDER CREATE] payment_lines_json raw value: '[]'
```
**This means**: JavaScript is not sending the payment data. The form submission didn't call recalcPayments() properly or the payment rows are not being read correctly.

### Issue B: amount=0 in payment processing
If you see:
```
[DEBUG ORDER CREATE] Processing payment #0: mode=cash, amount=0
[DEBUG ORDER CREATE] SKIPPING payment #0 because amount <= 0
```
**This means**: The payment data is being sent but with amount=0. Either:
- User didn't actually enter an amount (left it blank)
- JavaScript is reading blank values as 0

### Issue C: payment_count=0 at the end
If you see:
```
[DEBUG ORDER CREATE] Total payments created: 0
[DEBUG ORDER CREATE] Total OrderPayment objects for this order: 0
```
**This means**: Either the JSON was empty (Issue A) or all payments had amount=0 (Issue B).

## Files Modified in This Debug Session
- `/home/aryan/nirmalajewellers/order/forms.py` - Added clean() method with logging
- `/home/aryan/nirmalajewellers/order/templates/order/order_form.html` - Added extensive console.log() statements
- `/home/aryan/nirmalajewellers/order/views.py` - Added detailed payment processing logs
- `/home/aryan/nirmalajewellers/test_payment_submission.py` - Test script (verified form clean() works)

## Next Steps After Testing
Once you provide the debug output, I will:
1. Identify exactly where the payment data is being lost
2. Apply a targeted fix to that specific location
3. Test the fix
4. Verify orders now save with correct payment data

## Timeline
- Previous Phase: Daily Rates feature ✓ Complete
- Current Phase: Fix payment data persistence ← YOU ARE HERE
- Next Phase: Final verification and cleanup
