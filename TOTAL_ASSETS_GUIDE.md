# Total Assets Page - Quick Guide

## Overview
The **Total Assets** page provides a simple, clear view of all your physical assets and receivables in one place. It's designed to be easier to understand than the full balance sheet.

## What's Included

### 1. 💍 Ornament Inventory
Shows all ornaments currently in stock valued at today's rates:
- **Total ornaments count**: Number of pieces
- **Gold weight**: Total grams of gold in stock
- **Silver weight**: Total grams of silver in stock
- **Diamond weight**: Total grams of diamonds in stock
- **Values**: Gold, Silver, and Diamond amounts converted to rupees

**Example:**
- 50 ornaments
- 500 grams of gold @ ₹7000/gram = ₹35,00,000
- 200 grams of silver @ ₹80/gram = ₹16,000

### 2. 🪙 Raw Materials
Bulk metals not yet made into ornaments:
- **Raw gold value**: Unworked gold inventory
- **Raw silver value**: Unworked silver inventory

### 3. 💎 Stones
Total value of stones inventory at cost price.

### 4. 🧿 Motimala
Total value of motimala inventory at cost price.

### 5. 📿 Potey
Total value of potey inventory at cost price.

### 6. 📋 Order Receivables
Total amount that customers owe for pending orders (not yet converted to sales).

---

## How It's Calculated

| Component | Formula |
|-----------|---------|
| Ornament Gold Value | (Gold Weight in grams / 11.664) × Current Gold Rate |
| Ornament Silver Value | (Silver Weight in grams / 11.664) × Current Silver Rate |
| Ornament Diamond Value | (Diamond Weight in grams / 11.664) × Current Gold Rate* |
| Raw Metals | Quantity from metal stock × current rates |
| Other Inventory | Cost price from database |
| Order Receivables | Sum of pending order amounts |
| **TOTAL ASSETS** | **Sum of all above** |

*Note: Diamonds are valued at gold rate as a fallback

---

## Key Differences from Balance Sheet

| Feature | Total Assets Page | Balance Sheet |
|---------|------------------|---------------|
| **Purpose** | Show physical assets | Show complete financial position |
| **Complexity** | Simple, easy to understand | Complex accounting concepts |
| **Content** | Only assets + receivables | Assets, Liabilities, Equity |
| **Best For** | Quick asset overview | Financial analysis |

---

## Accessing the Page

1. Click on **Finance** menu in sidebar
2. Select **Total Assets** (new option at top)
3. View your complete asset breakdown

---

## What the Page Shows

### Asset Breakdown Table
Shows a percentage breakdown of your total assets:
- Which categories make up your wealth
- Quick visual of your portfolio composition

### Colors & Icons
- 💍 Blue = Ornament inventory
- 🪙 Green = Raw materials
- 💎 Cyan = Stones
- 🧿 Yellow = Motimala
- 📿 Red = Potey
- 📋 Gray = Receivables
- ✅ Green = Total Assets

---

## Understanding Your Assets

### Example Scenario
If your total assets are ₹1,00,00,000:
- 60% (₹60,00,000) = Ornament inventory
- 20% (₹20,00,000) = Raw materials
- 10% (₹10,00,000) = Stones, Motimala, Potey
- 10% (₹10,00,000) = Customer receivables

This tells you most of your wealth is in finished ornaments.

---

## Updates & Refresh

The page **automatically calculates** from:
- Current daily rates (updated via Daily Rates page)
- Current inventory (updated as you buy/sell)
- Current orders (updated as customers place orders)

Just visit the page anytime to see the latest totals!

---

## Tips

✅ **Check regularly** - Your assets change as you transact  
✅ **Update rates daily** - Ensures accurate valuations  
✅ **Track trends** - Visit often to see if total assets grow  
✅ **Use for planning** - Helps decide what to order/make  

---

## Need Help?

For detailed accounting explanation, see **BALANCE_SHEET_DETAILED_GUIDE.md**

For just the key concepts, see **BALANCE_SHEET_QUICK_REFERENCE.md**
