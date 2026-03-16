# Balance Sheet - Quick Reference Card

## 🎯 One-Minute Summary

The **Balance Sheet** answers: "What is my business worth RIGHT NOW?"

### The Equation
```
ASSETS (What You Own) = LIABILITIES (What You Owe) + EQUITY (What's Left)
```

### Real-World Analogy
Think of it like your personal situation:
- **Assets**: Your car, house, bank account = ₹100 lakh
- **Liabilities**: Your car loan, home loan = ₹60 lakh  
- **Equity**: Your actual wealth = ₹40 lakh

---

## 📊 The Three Parts

### 1. ASSETS 💰 = Things of Value You Own

In your jewellery business:
- **Debtors**: Customer money owed to you
- **Order Income**: Value of pending orders
- **Sales Income**: Revenue from completed sales

💡 **Think of it as**: What customers/orders owe you

---

### 2. LIABILITIES 🏦 = Debts You Must Pay

In your jewellery business:
- **Creditors**: Supplier money you owe
- **Salaries**: Employee payments pending
- **Expenses**: Business costs incurred

💡 **Think of it as**: What you must pay to others

---

### 3. EQUITY 👑 = Your Net Worth

Calculated as: **ASSETS - LIABILITIES**

💡 **Think of it as**: If you sold everything and paid debts, how much is left for you?

---

## 🔢 Quick Math Example

```
YOUR BUSINESS TODAY:

Assets:      ₹750,000  (Debtors ₹100k + Orders ₹250k + Sales ₹400k)
Liabilities: ₹400,000  (Creditors ₹200k + Salaries ₹150k + Expenses ₹50k)
Equity:      ₹350,000  (₹750,000 - ₹400,000)

✅ BALANCED: 750,000 = 400,000 + 350,000
```

---

## 🎨 Visual at a Glance

```
┌──────────┐         ┌──────────┐
│  ASSETS  │         │LIABILITY │
│  ₹750k   │    =    │  ₹400k   │  +  ┌────────┐
│          │         │          │     │ EQUITY │
└──────────┘         └──────────┘     │ ₹350k  │
                                      └────────┘
```

---

## 🔍 How to Read Your Balance Sheet

| Section | Shows | Questions It Answers |
|---------|-------|---------------------|
| **ASSETS** | What business owns | Do we have enough to sell? |
| **LIABILITIES** | What business owes | Can we pay what we owe? |
| **EQUITY** | Owner's net worth | Is business growing? |

---

## ⚡ Key Insights

### Positive Equity ✅
- Business is worth something
- More assets than debts
- Owner has stake in business

### Negative Equity ❌
- Debts exceed assets
- Business is underwater
- Needs immediate fix

### Growing Equity 📈
- Profits are accumulating
- Business is improving
- Good sign for future

### Shrinking Equity 📉
- Making losses
- Spending more than earning
- Take corrective action

---

## 💼 What to Do With This

### Management Decisions
- "Can we take a bank loan?" → Check equity ratio
- "Should we reduce staff?" → Check expense portion
- "Is business healthy?" → Check if equity is positive
- "Can we buy new equipment?" → Check total assets

### Strategic Planning
- Growing equity? → Time to expand
- Shrinking equity? → Time to cut costs
- High liabilities? → Focus on collections
- Low assets? → Focus on sales

---

## 🚀 Quick Checks

### Is Equity Healthy?
```
✅ If Equity = 40-60% of Assets → Good
⚠️  If Equity = 20-40% of Assets → Caution
❌ If Equity < 0                 → Problem
```

### Can We Pay Bills?
```
✅ If Assets ≥ 2× Liabilities → Good
⚠️  If Assets ≥ 1.5× Liabilities → Fair
❌ If Assets < Liabilities     → Problem
```

---

## 📍 Data Sources

| Item | Comes From |
|------|-----------|
| Debtors | DebtorTransaction table |
| Order Income | Order table |
| Sales Income | Order + Sale tables |
| Creditors | CreditorTransaction table |
| Salaries | EmployeeSalary table |
| Expenses | Expense table |

---

## 🔄 How It Updates

1. **You make a transaction** (sell, pay supplier, hire staff)
2. **Data saved to database**
3. **Balance sheet recalculates** automatically
4. **New numbers displayed** when you view it

---

## 📈 Three Scenarios

### Business A: Strong
```
Assets: ₹1,000,000
Liabilities: ₹300,000
Equity: ₹700,000
Status: ✅ Very Healthy
```

### Business B: Fair
```
Assets: ₹500,000
Liabilities: ₹250,000
Equity: ₹250,000
Status: ⚠️ Acceptable
```

### Business C: Weak
```
Assets: ₹200,000
Liabilities: ₹250,000
Equity: -₹50,000
Status: ❌ In Trouble
```

---

## 🎓 Important Formulas

```
Total Assets = Debtors + Orders + Sales
Total Liabilities = Creditors + Salaries + Expenses
Equity = Assets - Liabilities
Equity% = (Equity ÷ Assets) × 100
Debt% = (Liabilities ÷ Assets) × 100
```

---

## ❓ Common Questions

**Q: Why does it need to balance?**
A: It's the law of accounting! Everything must add up.

**Q: What if it doesn't balance?**
A: There's an error in the data. Check your transactions.

**Q: How often should I check?**
A: Weekly or monthly for best insights.

**Q: Is higher equity always better?**
A: Generally yes, but too high means not using resources efficiently.

**Q: Can I improve equity?**
A: Yes! Increase sales and reduce expenses.

---

## 🎯 Action Steps

1. **Check your balance sheet today**
   - URL: `/finance/balance-sheet/`

2. **Understand your equity**
   - Is it positive? Growing?

3. **Review your liabilities**
   - Are they manageable?

4. **Plan improvements**
   - Increase income
   - Reduce expenses
   - Collect from debtors

---

## 💡 Remember

```
Balance Sheet = Instant snapshot of business health
It tells you AT THIS MOMENT:
• How much you own
• How much you owe
• How much is yours
```

---

## 🔗 Learn More

- **Detailed Guide**: See BALANCE_SHEET_DETAILED_GUIDE.md
- **Visual Guide**: See BALANCE_SHEET_VISUAL_GUIDE.md
- **Your Data**: Go to `/finance/balance-sheet/`

---

**Last Updated**: January 27, 2026
**Time to Read**: 2 minutes
**Complexity**: Beginner-Friendly ✅

Print this card and keep it handy! 📋
