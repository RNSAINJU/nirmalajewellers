# ✅ Pre-Testing Checklist

Before running the debug test, make sure you have everything set up:

## Server & Environment

- [ ] Django development server is running at http://localhost:8000/
  - If not, run: `cd /home/aryan/nirmalajewellers && /home/aryan/venv/bin/python manage.py runserver`
- [ ] You can access the application in your browser
- [ ] You have a modern browser (Chrome, Firefox, Edge, Safari)

## Documentation

- [ ] Downloaded/opened all documentation files:
  - [ ] `START_HERE.md` (you read this first!)
  - [ ] `QUICK_DEBUG_TEST.md` (quick test guide)
  - [ ] `VISUAL_DEBUG_GUIDE.md` (expected outputs)
  - [ ] `DEBUG_README.md` (index)
- [ ] You understand the basic problem:
  - [ ] Payments are being saved as 0
  - [ ] We're adding logging to trace where data is lost

## Browser Setup

- [ ] Browser is set to http://localhost:8000/
- [ ] DevTools can be opened with F12
- [ ] You know how to access Console tab (F12 → Console)
- [ ] You know how to copy console text (right-click → "Save as..." or select & copy)

## Terminal Setup

- [ ] Terminal is visible/accessible where Django is running
- [ ] You can see the terminal output
- [ ] You know how to select and copy terminal text

## Test Procedure (Read This First!)

1. [ ] Open http://localhost:8000/order/create/
2. [ ] Press F12 to open DevTools
3. [ ] Click the "Console" tab
4. [ ] Fill in:
   - Customer Name: `Test Customer` (or any name)
   - Phone: `9841234567` (or any 7-15 digit number)
5. [ ] Find the Payment section (right side of form)
6. [ ] Enter payment:
   - Mode: Keep as `Cash` (default)
   - Amount: Enter `1000` (or any amount)
7. [ ] Look at browser console:
   - [ ] Do you see lines starting with `[FORM SUBMIT]`?
   - [ ] Do you see lines starting with `[DEBUG]`?
   - [ ] Copy all visible lines
8. [ ] Click "Save Order"
9. [ ] Look at Django terminal:
   - [ ] Do you see lines starting with `[DEBUG ORDER CREATE]`?
   - [ ] Do you see lines starting with `[FORM CLEAN]`?
   - [ ] Copy all visible lines
10. [ ] Wait for redirect to order list
11. [ ] Click on the newly created order
12. [ ] Check the payment information:
    - [ ] What is the "Payment Amount"? (0.00 or 1000.00?)
    - [ ] What is the "Payment Mode"? (Cash or something else?)
    - [ ] Are there any payment records in the database?

## What to Collect

Before responding, gather:

1. **Browser Console Output**
   - [ ] Copy all lines starting with `[FORM SUBMIT]` and `[DEBUG]`
   - Save to a text file or note

2. **Django Terminal Output**
   - [ ] Copy all lines starting with `[DEBUG`, `[FORM`, `[SUNDRY`, etc.
   - Save to a text file or note

3. **Order Details**
   - [ ] Screenshot or note of payment_amount value
   - [ ] Screenshot or note of payment_mode value
   - [ ] Count of OrderPayment records for this order

4. **Your Observations**
   - [ ] Did anything error out?
   - [ ] Did form submit successfully?
   - [ ] Did console have any red error messages?

## Expected Results

You should see ONE of these four outcomes:

**Outcome 1 - SUCCESS** ✅
- [ ] Console shows: `[FORM SUBMIT] payment_lines_json value: [{...`
- [ ] Terminal shows: `[DEBUG ORDER CREATE] Creating OrderPayment:`
- [ ] Order shows: payment_amount = 1000.00

**Outcome 2 - FRONTEND ISSUE** ❌
- [ ] Console shows: `[FORM SUBMIT] payment_lines_json value: []` (EMPTY)
- [ ] Terminal shows: `[DEBUG ORDER CREATE] payment_lines_json raw value: '[]'` (EMPTY)

**Outcome 3 - AMOUNT ISSUE** ❌
- [ ] Console shows: `[DEBUG] Row 0 RAW: ... amountInput?.value=""` (BLANK!)
- [ ] Terminal shows: `[DEBUG ORDER CREATE] SKIPPING payment #0 because amount <= 0`

**Outcome 4 - DATA LOSS** ❌
- [ ] Console shows: `[FORM SUBMIT] payment_lines_json: [{...` (HAS DATA)
- [ ] Terminal shows: `[DEBUG ORDER CREATE] payment_lines_json raw value: '[]'` (NO DATA)

---

## Common Issues & Solutions

**Issue**: "F12 doesn't open DevTools"  
**Solution**: Try Ctrl+Shift+I or right-click on page → "Inspect"

**Issue**: "I don't see any console output"  
**Solution**: 
- Reload the page (Ctrl+R or Cmd+R)
- Make sure Console tab is selected
- Look for "Clear console" button - click it to see only new messages

**Issue**: "Terminal is not visible"  
**Solution**: You might have run the server with `&` in background. It's running but you can't see output. Either:
- Restart terminal
- Or open new terminal and check Django logs

**Issue**: "Console shows errors"  
**Solution**: Take a screenshot! The error message will help identify the issue.

**Issue**: "Form won't submit"  
**Solution**: 
- Make sure you filled in customer name AND phone number
- Phone number must be 7-15 digits

---

## After Running the Test

1. [ ] Collect all output (console + terminal)
2. [ ] Note the final order values (payment_amount, payment_mode)
3. [ ] Create a new message with:
   - Console output
   - Terminal output
   - Order details
   - Any errors you saw

---

## Questions?

- Refer to `QUICK_DEBUG_TEST.md` for quick start
- Refer to `VISUAL_DEBUG_GUIDE.md` for expected outputs
- Refer to `DEBUG_PAYMENT_GUIDE.md` for detailed explanations

---

## Ready?

✅ All set! Follow `QUICK_DEBUG_TEST.md` to start the test.

Good luck! 🚀
