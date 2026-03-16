# Balance Sheet - Detailed Explanation

## 📊 Overview

The Balance Sheet is a financial statement that shows the financial position of Nirmala Jewellers at a specific point in time. It follows the fundamental accounting equation:

```
ASSETS = LIABILITIES + EQUITY
```

---

## 🏗️ Balance Sheet Structure

### Three Main Components:

```
┌─────────────────────────────────────────┐
│         BALANCE SHEET EQUATION          │
├─────────────────────────────────────────┤
│                                         │
│    ASSETS = LIABILITIES + EQUITY       │
│                                         │
│    What You Own = What You Owe + Value │
│                                         │
└─────────────────────────────────────────┘
```

---

## 1️⃣ ASSETS (What the Business Owns)

Assets are resources that have monetary value and are owned by the business.

### Current Assets in Your System:

#### **Debtors** 💰
- **What it is**: Money owed by customers who bought on credit
- **Example**: A customer bought gold ornament worth ₹50,000 but will pay in 30 days
- **Formula**: Sum of all unpaid customer invoices
- **In Code**: 
  ```python
  debtors = DebtorTransaction.objects.aggregate(total=Sum('amount'))['total']
  ```

#### **Order Income** 📦
- **What it is**: Revenue from orders placed but may not be completed
- **Example**: Total value of all orders created in the system
- **Formula**: Sum of all order totals
- **In Code**:
  ```python
  order_income = Order.objects.aggregate(total=Sum('total'))['total']
  ```

#### **Sales Income** 🛍️
- **What it is**: Revenue from completed sales
- **Example**: Orders that have been fulfilled and delivered to customers
- **Formula**: Sum of orders that have a related sale
- **In Code**:
  ```python
  sales_income = Order.objects.filter(sale__isnull=False).aggregate(total=Sum('total'))['total']
  ```

### **Total Assets Calculation**:
```
Total Assets = Debtors + Order Income + Sales Income
```

**Example:**
```
Debtors:        ₹100,000
Order Income:   ₹250,000
Sales Income:   ₹400,000
─────────────────────────
Total Assets:   ₹750,000
```

---

## 2️⃣ LIABILITIES (What the Business Owes)

Liabilities are obligations or debts that the business must pay to others.

### Current Liabilities in Your System:

#### **Creditors** 🏦
- **What it is**: Money owed by the business to suppliers
- **Example**: You bought gold from a supplier for ₹100,000 on credit
- **Formula**: Sum of all unpaid supplier invoices
- **In Code**:
  ```python
  creditors = CreditorTransaction.objects.aggregate(total=Sum('amount'))['total']
  ```

#### **Salaries** 👥
- **What it is**: Pending salary payments to employees
- **Example**: Employee salaries that have been earned but not yet paid
- **Formula**: Sum of all employee salary amounts
- **In Code**:
  ```python
  salaries = EmployeeSalary.objects.aggregate(total=Sum('total_salary'))['total']
  ```

#### **Expenses** 📋
- **What it is**: Business operating costs and expenses
- **Example**: Rent, utilities, marketing, transportation costs
- **Formula**: Sum of all expense amounts
- **In Code**:
  ```python
  expenses = Expense.objects.aggregate(total=Sum('amount'))['total']
  ```

### **Total Liabilities Calculation**:
```
Total Liabilities = Creditors + Salaries + Expenses
```

**Example:**
```
Creditors:        ₹200,000
Salaries:         ₹150,000
Expenses:         ₹50,000
──────────────────────────
Total Liabilities: ₹400,000
```

---

## 3️⃣ EQUITY (Net Worth)

Equity represents the owner's stake in the business - what remains after all liabilities are paid.

### Equity Calculation:
```
EQUITY = ASSETS - LIABILITIES
```

**Example with our numbers:**
```
Assets:           ₹750,000
Liabilities:     -₹400,000
──────────────────────────
Equity:           ₹350,000
```

**Meaning**: The business has ₹350,000 worth of net value.

---

## 🔄 Complete Balance Sheet Example

### Scenario:
Nirmala Jewellers' financial position on January 27, 2026

```
┌────────────────────────────────────────────────────────┐
│          NIRMALA JEWELLERS - BALANCE SHEET             │
│              As on January 27, 2026                    │
├──────────────────┬──────────────────────────────────────┤
│    ASSETS        │     Amount      │    LIABILITIES      │
├──────────────────┼─────────────────┼──────────────────────┤
│ Debtors          │  ₹100,000      │ Creditors      ₹200,000
│ Order Income     │  ₹250,000      │ Salaries       ₹150,000
│ Sales Income     │  ₹400,000      │ Expenses       ₹50,000
├──────────────────┼─────────────────┼──────────────────────┤
│ Total Assets     │  ₹750,000      │ Total Liabilities₹400,000
│                  │                 │                      │
│                  │                 │ EQUITY               │
│                  │                 │ (Assets - Liab)₹350,000
├──────────────────┴─────────────────┴──────────────────────┤
│ VERIFICATION: Assets (₹750,000) = Liabilities (₹400,000) + │
│ Equity (₹350,000) ✅ BALANCED                             │
└────────────────────────────────────────────────────────────┘
```

---

## 🧮 Code Flow - How Balance Sheet is Generated

### Step 1: Query Database
```python
# Get creditors (money owed to suppliers)
creditors = CreditorTransaction.objects.aggregate(total=Sum('amount'))['total']

# Get debtors (money customers owe us)
debtors = DebtorTransaction.objects.aggregate(total=Sum('amount'))['total']

# Get pending salaries
salaries = EmployeeSalary.objects.aggregate(total=Sum('total_salary'))['total']

# Get order income
order_income = Order.objects.aggregate(total=Sum('total'))['total']

# Get completed sales income
sales_income = Order.objects.filter(sale__isnull=False).aggregate(total=Sum('total'))['total']

# Get expenses
expenses = Expense.objects.aggregate(total=Sum('amount'))['total']
```

### Step 2: Calculate Totals
```python
# Calculate total assets
assets = debtors + order_income + sales_income

# Calculate total liabilities
liabilities = creditors + salaries + expenses

# Calculate equity
equity = assets - liabilities
```

### Step 3: Pass to Template
```python
context = {
    'assets': assets,
    'liabilities': liabilities,
    'equity': equity,
    'creditors': creditors,
    'debtors': debtors,
    'salaries': salaries,
    'order_income': order_income,
    'sales_income': sales_income,
    'expenses': expenses,
}
return render(request, 'finance/balance_sheet.html', context)
```

### Step 4: Display in HTML
Template shows all values in organized sections.

---

## 📈 Understanding the Numbers

### What Positive Equity Means ✅
```
Equity = ₹350,000 (Positive)
→ Business is solvent
→ Owner has positive net worth
→ Business is financially healthy
```

### What Negative Equity Means ❌
```
Equity = -₹50,000 (Negative)
→ Liabilities exceed assets
→ Business is insolvent
→ Business is in financial distress
```

---

## 🔍 Data Source Mapping

| Balance Sheet Item | Data Source | Model |
|---|---|---|
| Debtors | DebtorTransaction | Sundy Debtor payments |
| Order Income | Order | All orders created |
| Sales Income | Order + Sale | Completed sales |
| Creditors | CreditorTransaction | Sundry Creditor payments |
| Salaries | EmployeeSalary | Employee salary records |
| Expenses | Expense | Business expenses |

---

## 💡 Practical Examples

### Scenario 1: New Business Starting
```
Assets:         ₹0
Liabilities:    ₹0
Equity:         ₹0
(No transactions yet)
```

### Scenario 2: Business Making Sales
```
Assets:         ₹500,000 (from sales)
Liabilities:    ₹200,000 (creditors + salaries)
Equity:         ₹300,000 (Owner's value increased)
```

### Scenario 3: Business in Trouble
```
Assets:         ₹100,000
Liabilities:    ₹150,000 (borrowed more than earned)
Equity:         -₹50,000 (Negative! Needs intervention)
```

---

## ⚙️ How Data Flows Into Balance Sheet

```
┌─────────────────────────────────────────────────────┐
│           DATA FLOW IN YOUR SYSTEM                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Customer Makes Purchase                        │
│     ↓                                               │
│  2. Order Created (Order Income)                   │
│     ↓                                               │
│  3. Payment Received/Pending (Debtors)             │
│     ↓                                               │
│  4. Sale Recorded (Sales Income)                   │
│     ↓                                               │
│  5. Supplier Invoice (Creditors)                   │
│     ↓                                               │
│  6. Employee Salary Due (Salaries)                 │
│     ↓                                               │
│  7. Running Costs (Expenses)                       │
│     ↓                                               │
│  8. All Data Aggregated for Balance Sheet          │
│     ↓                                               │
│  9. Balance Sheet Calculated & Displayed           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Why Balance Sheet is Important

### 1. **Financial Health Check** 🏥
- Quickly see if business is profitable
- Identify if liabilities are growing too fast

### 2. **Decision Making** 📊
- Should we take a loan? (Check equity)
- Can we pay employees? (Check current assets)
- Should we reduce expenses? (Compare to income)

### 3. **Stakeholder Reporting** 📢
- Show bank for loans
- Show investors business value
- Demonstrate financial stability

### 4. **Tax & Compliance** 📋
- Tax authorities need balance sheet
- Audit trail for business records

---

## 🔐 Assumptions & Limitations

### Current Assumptions:
1. **All orders are assets** - May include cancelled orders
2. **All expenses are liabilities** - Prepaid expenses not handled separately
3. **Point-in-time snapshot** - Doesn't show trends over time

### Improvements to Consider:
1. Exclude cancelled orders from income
2. Separate fixed assets from current assets
3. Add historical balance sheet comparison
4. Add inventory valuation (gold/silver/diamond stocks)
5. Add cash position separately

---

## 📊 Balance Sheet Relationship

```
                    BALANCE SHEET
                         │
            ┌────────────┴────────────┐
            │                         │
         ASSETS                LIABILITIES + EQUITY
            │                         │
    ┌───────┴────────┐        ┌──────┴──────┐
    │                │        │             │
 Debtors      Order/Sales  Creditors    Salaries
                              │             │
                           Expenses       Equity
```

---

## 🚀 How to Use This Information

### For Owners:
1. Check **Equity** - Is your business value growing?
2. Compare **Assets vs Liabilities** - Are you over-leveraged?
3. Review **Expenses** - Can you reduce them?

### For Managers:
1. Use to justify **investment requests**
2. Monitor **creditor payments**
3. Plan **salary disbursements**

### For Finance Team:
1. Verify **accounting accuracy**
2. Prepare **financial reports**
3. Plan **cash flow**

---

## 📝 Formula Summary

```
════════════════════════════════════════════════════
                 BALANCE SHEET FORMULAS
════════════════════════════════════════════════════

ASSETS SIDE:
────────────
Debtors = Sum of all unpaid customer invoices
Order Income = Sum of all order totals
Sales Income = Sum of completed orders with sales
Total Assets = Debtors + Order Income + Sales Income

LIABILITIES SIDE:
─────────────────
Creditors = Sum of all unpaid supplier invoices
Salaries = Sum of all pending employee salaries
Expenses = Sum of all business expenses
Total Liabilities = Creditors + Salaries + Expenses

EQUITY SIDE:
────────────
Equity = Total Assets - Total Liabilities

VERIFICATION:
──────────────
Assets = Liabilities + Equity
(If this is true, balance sheet is BALANCED ✅)
════════════════════════════════════════════════════
```

---

## 🎓 Key Takeaways

1. **Balance Sheet = Snapshot**: Shows financial position at one moment
2. **Three-Part Structure**: Assets, Liabilities, Equity
3. **Must Balance**: Assets must equal Liabilities + Equity
4. **Tells a Story**: High equity = healthy business, Negative equity = problems
5. **Data-Driven**: All numbers come from actual transactions
6. **Decision Tool**: Use to make financial decisions

---

**URL to View Balance Sheet**: `/finance/balance-sheet/`

**Permission**: Requires login (staff/admin recommended)

**Frequency**: Can be viewed anytime to check current financial position

For more information, check the Finance module documentation!
