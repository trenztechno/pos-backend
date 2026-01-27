# Backend Testing Guide

**For Backend Developers: How to verify all endpoints and server functionality**

---

## Main Test File

**`verify_all_endpoints.py`** - This is your comprehensive test file!

This script tests **absolutely everything**:
- All models and their fields
- All URL patterns
- Authentication system
- Middleware configuration
- Logging system
- Storage configuration (local/S3)
- Serializers
- Views
- Admin configuration
- Sales rep interface
- **API endpoints with actual HTTP requests** (60+ test scenarios)

---

## How to Use

### Run the Test:

```bash
source venv/bin/activate
python verify_all_endpoints.py
```

### What It Does:

1. **Structural Tests** (1-10):
   - Checks if models exist and have correct fields
   - Verifies URL patterns are registered
   - Tests authentication configuration
   - Verifies middleware setup
   - Checks logging configuration
   - Tests storage settings
   - Verifies serializers are importable
   - Checks views are properly defined
   - Tests admin registration
   - Verifies sales rep interface

2. **API Endpoint Tests** (11):
   - Makes **actual HTTP requests** to all endpoints
   - Tests authentication flow
   - Tests CRUD operations for categories
   - Tests CRUD operations for items
   - Tests image uploads (multipart/form-data)
   - Tests sync endpoints
   - Tests sales backup (upload and download)
   - Tests settings push
   - Tests logout

### Expected Output:

```
======================================================================
  COMPREHENSIVE SERVER FUNCTIONALITY VERIFICATION
======================================================================

[Tests run...]

======================================================================
  SUMMARY
======================================================================
✓ PASS: Models
✓ PASS: URLs
✓ PASS: Authentication
✓ PASS: Middleware
✓ PASS: Logging
✓ PASS: Storage
✓ PASS: Serializers
✓ PASS: Views
✓ PASS: Admin
✓ PASS: Sales Rep Interface
✓ PASS: API Endpoints (HTTP)

======================================================================
Total: 11/11 tests passed
======================================================================

All functionality verified successfully!
```

---

## When to Run This

**Run this test file:**
- After making any changes to models
- After adding/modifying endpoints
- After changing authentication logic
- After updating views or serializers
- Before deploying to production
- After pulling new code
- When debugging issues

**Basically: Run it whenever you want to ensure everything works!**

---

## What Gets Tested

### 1. Models
- All model fields exist
- Relationships are correct
- Many-to-many relationships work

### 2. URLs
- All expected endpoints are registered
- URL patterns are correct

### 3. Authentication
- Token authentication configured
- Middleware setup correctly

### 4. Middleware
- CORS middleware
- Authentication middleware
- API logging middleware

### 5. Logging
- Loggers configured
- Audit log functions accessible
- Logs directory exists

### 6. Storage
- Media storage configured
- S3 toggle works (if enabled)

### 7. Serializers
- All serializers importable
- Image fields present

### 8. Views
- All views importable
- View methods exist

### 9. Admin
- Models registered in admin
- Admin classes exist

### 10. Sales Rep Interface
- Views importable
- Templates exist

### 11. API Endpoints (HTTP Requests) (65+ scenarios)

#### Authentication Tests
- **GET /health/** - Health check
- **POST /auth/register** - User registration (with FSSAI license)
- **POST /auth/login** - Login and get token (returns vendor data with fssai_license, logo_url, footer_note)
- **GET /auth/profile** - Get vendor profile (business details, logo URL)
- **PATCH /auth/profile** - Update vendor profile (business details)
- **PATCH /auth/profile** - Update vendor profile with logo upload (multipart/form-data)
- **POST /auth/forgot-password** - Verify username and GST number (valid case)
- **POST /auth/forgot-password** - Verify username and GST number (invalid GST)
- **POST /auth/forgot-password** - Verify username and GST number (mismatched username/GST)
- **POST /auth/forgot-password** - Verify username and GST number (pending vendor)
- **POST /auth/reset-password** - Reset password (valid case, invalidates old token)
- **POST /auth/reset-password** - Reset password (non-matching passwords)
- **POST /auth/reset-password** - Reset password (invalid GST)
- **POST /auth/logout** - Logout (deletes token)
 - **POST /auth/vendor/users/create** - Vendor owner creates staff user
 - **GET /auth/vendor/users** - List owner + staff users for vendor
 - **POST /auth/vendor/users/<user_id>/reset-password** - Owner resets staff password
 - **DELETE /auth/vendor/users/<user_id>** - Owner deactivates staff user

#### Category Tests
- **GET /items/categories/** - Get categories
- **GET /items/categories/?is_active=true** - Get active categories
- **POST /items/categories/** - Create category
- **GET /items/categories/<uuid>/** - Get category detail
- **PATCH /items/categories/<uuid>/** - Update category
- **DELETE /items/categories/<uuid>/** - Delete category
- **POST /items/categories/sync** - Batch sync categories

#### Item Tests
- **GET /items/** - Get items
- **GET /items/?category=<uuid>** - Get items filtered by category
- **GET /items/?search=<term>** - Search items
- **GET /items/?is_active=true** - Get active items
- **POST /items/** - Create item (JSON, without image)
- **POST /items/** - Create item with image upload (multipart/form-data)
- **GET /items/<uuid>/** - Get item detail
- **PATCH /items/<uuid>/** - Update item (JSON)
- **PATCH /items/<uuid>/** - Update item with image upload (multipart/form-data)
- **PATCH /items/<uuid>/status/** - Update item status
- **DELETE /items/<uuid>/** - Delete item
- **POST /items/sync** - Batch sync items

#### Inventory Tests
- **GET /inventory/unit-types/** - Get unit types
- **GET /inventory/** - Get inventory items
- **GET /inventory/?is_active=true** - Get active inventory items
- **GET /inventory/?search=<term>** - Search inventory items
- **GET /inventory/?low_stock=true** - Get low stock items
- **POST /inventory/** - Create inventory item
- **GET /inventory/<uuid>/** - Get inventory item detail
- **PATCH /inventory/<uuid>/** - Update inventory item
- **PATCH /inventory/<uuid>/stock/** - Update stock (add action)
- **PATCH /inventory/<uuid>/stock/** - Update stock (subtract action)
- **DELETE /inventory/<uuid>/** - Delete inventory item

#### Sales Backup Tests
- **GET /backup/sync** - Download bills from server (bi-directional sync)
  - Query params: `since`, `limit`, `billing_mode`, `start_date`, `end_date`
- **GET /backup/sync?billing_mode=gst** - Download GST bills only
- **GET /backup/sync?billing_mode=non_gst** - Download Non-GST bills only
- **GET /backup/sync?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD** - Download bills by date range
- **POST /backup/sync** - Upload Non-GST bill (basic)
- **POST /backup/sync** - Upload GST bill (intra-state with CGST + SGST)
- **POST /backup/sync** - Upload GST bill (inter-state with IGST)
- **POST /backup/sync** - Upload Non-GST bill
- **POST /backup/sync** - Upload batch of bills (multiple bills)
- **POST /backup/sync** - Upload duplicate bill (same invoice_number, should skip)
- **POST /backup/sync** - Upload bill with minimal data (only required fields)
- **POST /backup/sync** - Upload bill with linked items (item_id present)
- **POST /backup/sync** - Upload bill with additional items (no item_id)

#### Settings Tests
- **POST /settings/push** - Push device settings

#### Dashboard Tests
- **GET /dashboard/stats** - Overall dashboard statistics
- **GET /dashboard/stats?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD** - Dashboard stats with date range
- **GET /dashboard/sales** - Sales analytics
- **GET /dashboard/sales?billing_mode=gst** - Sales analytics filtered by GST bills
- **GET /dashboard/sales?billing_mode=non_gst** - Sales analytics filtered by Non-GST bills
- **GET /dashboard/items?sort=most_sold** - Most sold items
- **GET /dashboard/items?sort=least_sold** - Least sold items
- **GET /dashboard/payments** - Payment mode analytics
- **GET /dashboard/tax** - Tax collection analytics
- **GET /dashboard/profit** - Net profit calculation
- **GET /dashboard/dues** - Pending payments and dues
- **GET /dashboard/dues?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD** - Pending payments with date range

**Total: 66+ test scenarios covering all endpoints, all billing modes, all payment modes, all GST percentages, image uploads, edge cases, and error handling**

#### Complete Test Coverage

**Billing Modes Tested:**
- ✅ GST bills (intra-state: CGST + SGST)
- ✅ GST bills (inter-state: IGST only)
- ✅ Non-GST bills

**Payment Modes Tested:**
- ✅ Cash payment
- ✅ UPI payment (with payment_reference)
- ✅ Card payment (with payment_reference)
- ✅ Credit payment (pending payment)
- ✅ Other payment methods

**GST Percentages Tested:**
- ✅ 0% GST
- ✅ 5% GST
- ✅ 8% GST
- ✅ 18% GST
- ✅ Custom GST percentages

**Price Types Tested:**
- ✅ Exclusive pricing (GST not included in MRP)
- ✅ Inclusive pricing (GST included in MRP)

**Item Scenarios Tested:**
- ✅ Items with images (multipart/form-data upload)
- ✅ Items without images
- ✅ Veg items
- ✅ Non-veg items
- ✅ Items with multiple categories
- ✅ Items with additional discount
- ✅ Items without additional discount

**Bill Scenarios Tested:**
- ✅ Bills with linked items (item_id present)
- ✅ Bills with additional items (no item_id)
- ✅ Bills with mixed items (some linked, some additional)
- ✅ Bills with discounts
- ✅ Bills without discounts
- ✅ Bills with multiple items (different GST percentages)

---

## Default Setup Verification

**`verify_default_setup.py`** - Verify all default accounts and test data are present

### Run the Verification:

```bash
source venv/bin/activate
python verify_default_setup.py
```

### What It Verifies:

1. **Default Accounts:**
   - Admin: admin / admin123
   - Sales Rep: salesrep1 / salesrep123
   - Vendor 1: vendor1 / vendor123 (ABC Store)
   - Vendor 2: vendor2 / vendor123 (XYZ Restaurant)
   - Mobile Dev: mobiledev / mobile123 (Mobile Dev Restaurant)

2. **Test Data:**
   - Categories (global and vendor-specific)
   - Items (with GST fields and images)
   - Bills (GST and Non-GST)

3. **Mobile Developer Data:**
   - 15+ items with images
   - 8 categories
   - Sample bills (GST and Non-GST)
   - Vendor logo and FSSAI license

4. **API Access:**
   - Login with default credentials
   - API access with tokens
   - Image URLs accessibility

### Expected Output:

```
======================================================================
  DEFAULT SETUP VERIFICATION
======================================================================

======================================================================
  1. Verifying Default Accounts
======================================================================
✓ Admin account: admin / admin123 (Superuser)
✓ Sales Rep account: salesrep1 / salesrep123 (Active)
✓ Vendor 1: vendor1 / vendor123 (ABC Store, Approved)
✓ Vendor 2: vendor2 / vendor123 (XYZ Restaurant, Approved)
✓ Mobile Dev: mobiledev / mobile123 (Mobile Dev Restaurant, Approved)

======================================================================
  2. Verifying Test Data
======================================================================
  Total Categories: 15
✓ Global Categories: 3 found
✓ Vendor-Specific Categories: 12 found
  Total Items: 22
✓ Items with GST fields (mrp_price): 15
✓ Items with images: 15

======================================================================
  3. Verifying Mobile Developer Data
======================================================================
✓ Categories: 9 available (expected: 6+)
✓ Items: 15 found (expected: 15+)
✓ Items with complete GST fields: 15
✓ Items with images: 15
✓ Sample Bills: 2 found
  - GST Bills: 1
  - Non-GST Bills: 1

======================================================================
  4. Verifying API Access
======================================================================
✓ Vendor 1 login successful
✓ Vendor 1 API access working
✓ Mobile Dev login successful
✓ Mobile Dev API access working (15 items)

======================================================================
  VERIFICATION SUMMARY
======================================================================
PASS: Default Accounts
PASS: Test Data
PASS: Mobile Dev Data
PASS: API Access
PASS: Image URLs

Total: 5/5 checks passed
```

**Use this script to confirm to developers that all default accounts and data mentioned in documentation are present.**

---

## Troubleshooting

### If tests fail:

1. **Check the error message** - It will tell you what's wrong
2. **Check imports** - Make sure all imports are correct
3. **Check database** - Make sure migrations are run
4. **Check settings** - Verify all settings are configured

### Common Issues:

- **404 errors on detail endpoints**: This might be due to vendor isolation - the test creates a temporary vendor, so detail endpoints might not find resources created by other vendors. This is expected behavior.

- **Import errors**: Make sure all dependencies are installed (`pip install -r requirements.txt`)

- **Database errors**: Make sure PostgreSQL is running and migrations are applied

---

## Notes

- The test creates a temporary test user and vendor
- Test data is cleaned up after tests complete
- Some 404 errors on detail endpoints are expected (vendor isolation)
- The test uses Django's test client (APIClient) for HTTP requests
- Image upload tests use PIL to generate test images

---

## Quick Command

**Just run this whenever you make changes:**

```bash
source venv/bin/activate && python verify_all_endpoints.py
```

**That's it!** This one command verifies everything is working correctly.

---

**This is your go-to test file for ensuring all server functionality works!**
