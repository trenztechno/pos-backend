# Test Accounts & Credentials

**For Mobile App Developers & Testers**

All accounts are automatically created when backend team runs `./setup.sh`

**📱 Mobile App Developers:** See [MOBILE_APP_GUIDE.md](MOBILE_APP_GUIDE.md) first!

---

## 👨‍💼 Admin & Sales Rep

### Admin
- **Username:** `admin`
- **Password:** `admin123`
- **Access:** Django Admin Panel (`http://localhost:8000/admin/`)
- **Purpose:** Full system access, can approve vendors, manage all data

### Sales Rep
- **Username:** `salesrep1`
- **Password:** `salesrep123`
- **Access:** Sales Rep Interface (`http://localhost:8000/sales-rep/`)
- **Purpose:** Approve/reject vendors, view vendor list

---

## ✅ Approved Vendors (Ready to Use API)

These vendors are **already approved** and can login immediately to test the API.

### Vendor 1 - ABC Store
- **Username:** `vendor1`
- **Password:** `vendor123`
- **Business Name:** ABC Store
- **GST Number:** `29ABCDE1234F1Z5`
- **Status:** ✅ Approved & Active
- **Test Data:**
  - Categories: Breakfast, Lunch, Dinner (vendor-specific) + Drinks, Snacks (global)
  - Items: Coca Cola, Pepsi, Sandwich, Burger
  - Items have categories assigned

### Vendor 2 - XYZ Restaurant
- **Username:** `vendor2`
- **Password:** `vendor123`
- **Business Name:** XYZ Restaurant
- **GST Number:** `27XYZAB5678G2H6`
- **Status:** ✅ Approved & Active
- **Test Data:**
  - Categories: Appetizers, Main Course, Desserts (vendor-specific) + Drinks, Snacks (global)
  - Items: Pasta, Pizza, Ice Cream
  - Items have categories assigned

---

## ⏳ Pending Vendor (For Testing Approval Flow)

### Pending Vendor
- **Username:** `pendingvendor`
- **Password:** `pending123`
- **Business Name:** Pending Business
- **GST Number:** `19PENDING9999X9Y9`
- **Status:** ⏳ Pending Approval
- **Purpose:** Test the approval workflow
  - Try to login → Should get "pending approval" message
  - Approve via Sales Rep UI or Admin Panel
  - Then can login and use API

---

## 🔑 Getting Authentication Tokens

### Method 1: Login via API
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"vendor1","password":"vendor123"}'
```

Response:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "username": "vendor1",
  "message": "Login successful"
}
```

### Method 2: Use Token in API Calls
```bash
curl -X GET http://localhost:8000/items/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

---

## 📦 Test Data Summary

### Categories Created
- **Global Categories** (available to all vendors):
  - Drinks
  - Snacks

- **Vendor 1 Categories:**
  - Breakfast
  - Lunch
  - Dinner

- **Vendor 2 Categories:**
  - Appetizers
  - Main Course
  - Desserts

### Items Created

**Vendor 1 (ABC Store):**
- Coca Cola (₹25.00) - Categories: Drinks, Breakfast
- Pepsi (₹25.00) - Categories: Drinks
- Sandwich (₹50.00) - Categories: Breakfast, Lunch
- Burger (₹80.00) - Categories: Lunch

**Vendor 2 (XYZ Restaurant):**
- Pasta (₹120.00) - Categories: Main Course
- Pizza (₹150.00) - Categories: Main Course
- Ice Cream (₹60.00) - Categories: Desserts

---

## 🧪 Quick Test Scenarios

### 1. Test Approved Vendor Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"vendor1","password":"vendor123"}'
```
**Expected:** Success with token

### 2. Test Pending Vendor Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"pendingvendor","password":"pending123"}'
```
**Expected:** "pending approval" error message

### 3. Test Get Items (with token)
```bash
# First get token from login, then:
curl -X GET http://localhost:8000/items/ \
  -H "Authorization: Token YOUR_TOKEN"
```
**Expected:** List of items for that vendor

### 4. Test Get Categories
```bash
curl -X GET http://localhost:8000/items/categories/ \
  -H "Authorization: Token YOUR_TOKEN"
```
**Expected:** List of categories (vendor-specific + global)

### 5. Test Create Item
```bash
curl -X POST http://localhost:8000/items/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Item",
    "price": "100.00",
    "stock_quantity": 50,
    "category_ids": ["CATEGORY_UUID_HERE"]
  }'
```

### 6. Test Password Reset Flow
```bash
# Step 1: Verify GST number
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"gst_no": "29ABCDE1234F1Z5"}'
```
**Expected:** Success with business name and username

```bash
# Step 2: Reset password
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "gst_no": "29ABCDE1234F1Z5",
    "new_password": "newpassword123",
    "new_password_confirm": "newpassword123"
  }'
```
**Expected:** Password reset successful message

### 7. Test Approval Flow
1. Login as sales rep: `http://localhost:8000/sales-rep/`
2. View pending vendors
3. Approve `pendingvendor`
4. Try to login as `pendingvendor` → Should work now

---

## 🔄 Recreating Test Data

If you need to recreate test data:

```bash
source venv/bin/activate
python create_test_data.py
```

This will:
- Create/update test vendors
- Create/update test categories
- Create/update test items
- Ensure all tokens are created

---

## 📝 Notes

- **All passwords are simple for testing** (vendor123, admin123, etc.)
- **Tokens are automatically created** when users are created
- **Test data is safe to delete** - you can recreate it anytime
- **Vendor isolation:** Each vendor only sees their own data
- **Multi-category support:** Items can belong to multiple categories

---

**Last Updated:** 2024-01-01

