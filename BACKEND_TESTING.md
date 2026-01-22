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

### 11. API Endpoints (HTTP Requests) (60+ scenarios)
- **GET /health/** - Health check
- **POST /auth/register** - User registration (with FSSAI license)
- **POST /auth/login** - Login and get token (returns vendor data with fssai_license, logo_url, footer_note)
- **POST /auth/forgot-password** - Verify username and GST number
- **POST /auth/reset-password** - Reset password (invalidates old token)
- **POST /auth/logout** - Logout (deletes token)
- **GET /items/categories/** - Get categories
- **POST /items/categories/** - Create category
- **GET /items/categories/<uuid>/** - Get category detail
- **PATCH /items/categories/<uuid>/** - Update category
- **DELETE /items/categories/<uuid>/** - Delete category
- **POST /items/categories/sync** - Batch sync categories
- **GET /items/** - Get items (with filters: category, search, is_active)
- **POST /items/** - Create item (with GST fields: mrp_price, price_type, gst_percentage, veg_nonveg)
- **POST /items/** - Create item with image upload (multipart/form-data)
- **GET /items/<uuid>/** - Get item detail
- **PATCH /items/<uuid>/** - Update item
- **PATCH /items/<uuid>/** - Update item with image upload (multipart/form-data)
- **PATCH /items/<uuid>/status/** - Update item status
- **DELETE /items/<uuid>/** - Delete item
- **POST /items/sync** - Batch sync items
- **GET /inventory/unit-types/** - Get unit types
- **GET /inventory/** - Get inventory items (with filters)
- **POST /inventory/** - Create inventory item
- **GET /inventory/<uuid>/** - Get inventory item detail
- **PATCH /inventory/<uuid>/** - Update inventory item
- **PATCH /inventory/<uuid>/stock/** - Update stock (set/add/subtract)
- **DELETE /inventory/<uuid>/** - Delete inventory item
- **GET /backup/sync** - Download bills from server (bi-directional sync)
  - Query params: since, limit, billing_mode, start_date, end_date
- **POST /backup/sync** - Upload bills (GST and Non-GST, single or batch)
  - Tests: duplicate handling, minimal data, item linking
- **POST /settings/push** - Push device settings

**Total: 60+ test scenarios covering all endpoints, image uploads, edge cases, and error handling**

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
