# Bills and Dashboard Demo Guide

## 📋 What Was Added

### 1. Bills Added to `create_test_data.py`

**New Function:** `create_test_bills(vendor1, vendor2)`

**What it creates:**
- **GST Bills** for vendor1 and vendor2
- **Non-GST Bills** for vendor1
- **Bills with different payment modes** (Cash, UPI, Card)
- **Bills for different dates** (Today, Yesterday) for dashboard date range testing
- **BillItems** linked to actual items

**Bill Details:**
- Invoice numbers: `INV-2024-001`, `INV-2024-002`, etc.
- Bill numbers: `BN-2024-001`, `BN-2024-002`, etc.
- Complete GST breakdown (CGST, SGST)
- Payment modes: cash, upi, card
- Linked to actual items with quantities

---

### 2. Enhanced `verify_default_setup.py`

**New Function:** `verify_dashboard_data()`

**What it verifies:**
- ✅ All 6 dashboard endpoints work
- ✅ Dashboard stats returns correct data
- ✅ Dashboard sales with filters
- ✅ Dashboard items (most/least sold)
- ✅ Dashboard payments (payment split)
- ✅ Dashboard tax (tax collection)
- ✅ Dashboard profit (profit calculation)

**Enhanced Bill Verification:**
- Checks bills for all vendors
- Verifies bill items count
- Shows bill breakdown by vendor

---

## 🚀 How to Use

### Step 1: Populate Test Data with Bills

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the script
python3 create_test_data.py
```

**What it does:**
- Creates vendors (vendor1, vendor2, pendingvendor)
- Creates categories
- Creates items
- **Creates bills** (GST and Non-GST) ← NEW!

**Output Example:**
```
🧾 Creating test bills...
  ✓ Created GST Bill for ABC Store: INV-2024-001 (₹236.00)
  ✓ Created Non-GST Bill for ABC Store: INV-2024-002 (₹200.00)
  ✓ Created Yesterday's Bill: INV-2024-003
  ✓ Created Bill for XYZ Restaurant: INV-2024-001 (₹354.00)

  ✅ Created test bills for dashboard testing
```

---

### Step 2: Populate Mobile Dev Data (Already has bills)

```bash
python3 populate_mobile_dev_data.py
```

**What it does:**
- Creates mobiledev vendor
- Creates 15+ items with images
- Creates categories (Breakfast, Lunch, Dinner, etc.)
- **Creates 2 sample bills** (1 GST, 1 Non-GST) ← Already had this!

---

### Step 3: Verify Everything

```bash
python3 verify_default_setup.py
```

**What it verifies:**
- ✅ Default accounts
- ✅ Test data (categories, items)
- ✅ Mobile dev data
- ✅ API access
- ✅ **Dashboard endpoints** ← NEW!
- ✅ Image URLs

**Output Example:**
```
======================================================================
  5. Verifying Dashboard Data
======================================================================
✓ Dashboard Stats: Working
  - Total Bills: 5
  - Total Revenue: ₹1500.00
  - Payment Split: 5 modes
✓ Dashboard Sales: Working
✓ Dashboard Items: Working (10 items returned)
✓ Dashboard Payments: Working (3 payment modes)
✓ Dashboard Tax: Working
  - Total Tax: ₹270.00
✓ Dashboard Profit: Working
  - Net Profit: ₹600.00
```

---

## 📊 Dashboard Examples

### Example 1: Get Overall Stats (Today)

```bash
curl -X GET "http://localhost:8000/dashboard/stats/" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response:**
```json
{
  "vendor_id": "...",
  "vendor_name": "ABC Store",
  "date_range": {
    "start_date": "2024-01-21",
    "end_date": "2024-01-21"
  },
  "statistics": {
    "total_bills": 3,
    "gst_bills": 2,
    "non_gst_bills": 1,
    "total_revenue": "1180.00",
    "total_tax_collected": "180.00",
    "payment_split": {
      "cash": {"count": 2, "amount": "800.00"},
      "upi": {"count": 1, "amount": "200.00"},
      "card": {"count": 0, "amount": "0.00"}
    }
  }
}
```

---

### Example 2: Get Sales Analytics (Date Range + GST Filter)

```bash
curl -X GET "http://localhost:8000/dashboard/sales/?start_date=2024-01-01&end_date=2024-01-31&billing_mode=gst" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response:**
```json
{
  "summary": {
    "total_bills": 10,
    "total_revenue": "35000.00",
    "total_tax": "5338.98",
    "total_cgst": "2669.49",
    "total_sgst": "2669.49"
  },
  "daily_breakdown": [
    {
      "date": "2024-01-21",
      "bills_count": 2,
      "revenue": "7000.00",
      "tax": "1067.80"
    },
    {
      "date": "2024-01-20",
      "bills_count": 1,
      "revenue": "3500.00",
      "tax": "533.90"
    }
  ]
}
```

---

### Example 3: Get Most Sold Dishes

```bash
curl -X GET "http://localhost:8000/dashboard/items/?sort=most_sold&limit=5" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response:**
```json
{
  "items": [
    {
      "item_name": "Coca Cola",
      "total_quantity": "150.00",
      "total_revenue": "3750.00",
      "bill_count": 120,
      "item_id": "...",
      "category": ["Beverage"],
      "veg_nonveg": "veg"
    },
    {
      "item_name": "Pizza Margherita",
      "total_quantity": "80.00",
      "total_revenue": "8000.00",
      "bill_count": 75
    }
  ]
}
```

---

### Example 4: Get Payment Split

```bash
curl -X GET "http://localhost:8000/dashboard/payments/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response:**
```json
{
  "summary": {
    "total_transactions": 50,
    "total_revenue": "50000.00"
  },
  "payment_split": [
    {
      "payment_mode": "cash",
      "transaction_count": 30,
      "total_amount": "30000.00",
      "percentage": "60.00"
    },
    {
      "payment_mode": "upi",
      "transaction_count": 15,
      "total_amount": "15000.00",
      "percentage": "30.00"
    },
    {
      "payment_mode": "card",
      "transaction_count": 5,
      "total_amount": "5000.00",
      "percentage": "10.00"
    }
  ]
}
```

---

### Example 5: Get Tax Collected

```bash
curl -X GET "http://localhost:8000/dashboard/tax/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response:**
```json
{
  "summary": {
    "gst_bills_count": 30,
    "total_tax_collected": "9000.00",
    "cgst_collected": "4500.00",
    "sgst_collected": "4500.00"
  },
  "tax_by_percentage": [
    {
      "gst_percentage": "18.00",
      "item_count": 150,
      "tax_collected": "5400.00"
    },
    {
      "gst_percentage": "5.00",
      "item_count": 80,
      "tax_collected": "2500.00"
    }
  ]
}
```

---

### Example 6: Get Profit Calculation

```bash
curl -X GET "http://localhost:8000/dashboard/profit/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response:**
```json
{
  "profit_calculation": {
    "total_revenue": "50000.00",
    "estimated_cost": "30000.00",
    "estimated_cost_percentage": "60.00",
    "net_profit": "20000.00",
    "profit_margin_percentage": "40.00"
  },
  "note": "Profit calculation is estimated based on 60% cost assumption..."
}
```

---

## 🧪 Testing the Dashboard

### Quick Test Script

```python
import requests

BASE_URL = 'http://localhost:8000'
TOKEN = 'YOUR_TOKEN_HERE'

headers = {'Authorization': f'Token {TOKEN}'}

# Test all dashboard endpoints
endpoints = [
    '/dashboard/stats/',
    '/dashboard/sales/',
    '/dashboard/items/?sort=most_sold',
    '/dashboard/payments/',
    '/dashboard/tax/',
    '/dashboard/profit/'
]

for endpoint in endpoints:
    response = requests.get(f'{BASE_URL}{endpoint}', headers=headers)
    print(f"{endpoint}: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Working - {len(str(data))} bytes of data")
    else:
        print(f"  ❌ Failed: {response.text}")
```

---

## 📝 Summary of Changes

### Files Modified:

1. **`create_test_data.py`**
   - ✅ Added `create_test_bills()` function
   - ✅ Creates GST and Non-GST bills
   - ✅ Creates bills with different payment modes
   - ✅ Creates bills for different dates

2. **`verify_default_setup.py`**
   - ✅ Added `verify_dashboard_data()` function
   - ✅ Tests all 6 dashboard endpoints
   - ✅ Enhanced bill verification
   - ✅ Shows bill counts per vendor

3. **`populate_mobile_dev_data.py`**
   - ✅ Already had `create_sample_bills()` function
   - ✅ Creates 2 sample bills (GST + Non-GST)

---

## 🎯 What You Can Test Now

1. **Run populate scripts:**
   ```bash
   python3 create_test_data.py        # Creates bills for vendor1, vendor2
   python3 populate_mobile_dev_data.py  # Creates bills for mobiledev
   ```

2. **Verify everything:**
   ```bash
   python3 verify_default_setup.py   # Verifies all data including dashboard
   ```

3. **Test dashboard endpoints:**
   - Use the examples above with cURL or Postman
   - All endpoints return real data from the bills you created

4. **Test with different date ranges:**
   ```bash
   # Today only
   /dashboard/stats/
   
   # Last 7 days
   /dashboard/stats/?start_date=2024-01-14&end_date=2024-01-21
   
   # Last month
   /dashboard/stats/?start_date=2024-01-01&end_date=2024-01-31
   ```

---

## ✅ Expected Results

After running the scripts, you should have:

- **vendor1**: 2-3 bills (GST + Non-GST, different payment modes)
- **vendor2**: 1-2 bills (GST)
- **mobiledev**: 2 bills (GST + Non-GST)

**Total:** 5-7 bills across all vendors

**Dashboard will show:**
- Total bills count
- Revenue from all bills
- Tax collected (from GST bills)
- Payment split (Cash/UPI/Card)
- Most/least sold items
- Profit calculation

All ready to test! 🚀

