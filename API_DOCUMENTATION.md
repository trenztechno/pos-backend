# Complete API Documentation

**📱 Mobile App Developers:** See [MOBILE_APP_GUIDE.md](MOBILE_APP_GUIDE.md) first for quick start guide!

**Base URL:** `http://localhost:8000` (or your server URL)

**Authentication:** All endpoints (except `/health/`, `/auth/login`, `/auth/register`, `/auth/forgot-password`, and `/auth/reset-password`) require Token Authentication.

**Token Permanence:** Authentication tokens are **permanent and never expire automatically**. Users stay logged in indefinitely unless they explicitly logout. The same token is reused on each login - tokens are only deleted when:
- User explicitly logs out (POST /auth/logout)
- Password is reset (for security)
- Staff user is removed by owner

**Billing Modes:** The system supports per-bill billing modes (not vendor-specific):
- **GST Billing** (`"gst"`): GST calculations are applied to the bill (CGST, SGST for intra-state; IGST for inter-state). Tax is calculated per item using HSN codes, or vendor-level SAC code if configured.
- **Non-GST Billing** (`"non_gst"`): No GST calculations are applied

Each bill can be either GST or Non-GST. The `billing_mode` field in the bill data determines how taxes are calculated. Vendors can create both types of bills.

**Image URLs (Pre-Signed URLs):** 
- **For Upload:** You send image files directly to the server (multipart/form-data) - no pre-signed URL needed
- **For Download/View:** All image URLs (`image_url` for items, `logo_url` for vendors) are returned as **pre-signed URLs** when using S3 storage
- Pre-signed URLs are temporary, secure URLs that expire after 1 hour (configurable)
- This provides secure access without requiring public bucket access
- See [PRESIGNED_URLS_GUIDE.md](PRESIGNED_URLS_GUIDE.md) for details

---

## Table of Contents

1. [Health Check](#health-check)
2. [Authentication](#authentication)
   - [Register New Vendor](#register-new-vendor)
   - [Login](#login)
   - [Logout](#logout)
   - [Forgot Password](#forgot-password-verify-username-and-phone-number)
   - [Reset Password](#reset-password)
3. [Vendor Registration & Approval](#vendor-registration--approval)
4. [Categories](#categories)
5. [Items](#items)
   - [Get All Items](#get-all-items)
   - [Create Item](#create-item)
   - [Upload Item Image](#upload-item-image)
   - [Update Item Image](#update-item-image)
   - [Get Item Details](#get-item-details)
   - [Update Item](#update-item)
6. [Inventory Management](#inventory-management)
7. [Complete Sync Architecture (Bi-Directional)](#complete-sync-architecture-bi-directional)
   - [Reverse Sync Endpoints (Server → Mobile)](#reverse-sync-endpoints-server--mobile)
   - [Forward Sync Endpoints (Mobile → Server)](#forward-sync-endpoints-mobile--server)
8. [Bills (Direct CRUD Operations)](#bills-direct-crud-operations)
   - [List Bills](#list-bills)
   - [Create Bill](#create-bill)
   - [Get Bill Details](#get-bill-details)
   - [Update Bill](#update-bill)
   - [Delete Bill](#delete-bill)
9. [Sales Backup (Multi-Device Sync Only)](#sales-backup-multi-device-sync-only)
10. [Dashboard & Analytics](#dashboard--analytics)
   - [Dashboard Stats](#dashboard-stats)
   - [Sales Analytics](#sales-analytics)
   - [Item Analytics](#item-analytics)
   - [Payment Analytics](#payment-analytics)
   - [Tax Analytics](#tax-analytics)
   - [Profit Analytics](#profit-analytics)
   - [Pending Payments & Dues](#pending-payments--dues)
10. [Settings](#settings)
11. [Error Responses](#error-responses)

---

## Default Test Credentials

**⚠️ Important:** All examples in this documentation use these default test credentials created by `setup.sh` and `create_test_data.py`.

### Admin & Sales Rep
- **Admin:** `admin` / `admin123` (Django Admin: `http://localhost:8000/admin/`)
- **Sales Rep:** `salesrep1` / `salesrep123` (Sales Rep Interface: `http://localhost:8000/sales-rep/`)

### Approved Vendors (Ready to Use)
- **Vendor 1:** `vendor1` / `vendor123` (ABC Store, GST: `29ABCDE1234F1Z5`)
- **Vendor 2:** `vendor2` / `vendor123` (XYZ Restaurant, GST: `27XYZAB5678G2H6`)

### Pending Vendor (For Testing)
- **Pending Vendor:** `pendingvendor` / `pending123` (Pending Business, GST: `19PENDING9999X9Y9`)

**Note:** All login examples use `vendor1` / `vendor123`. Registration examples use generic credentials for NEW vendors (not the test accounts).

---

## Health Check

### Check Server Status

**GET** `/health/`

**No authentication required**

Returns server health status, database connectivity, and system information. Useful for monitoring, load balancers, and mobile app connectivity checks.

**Success Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-01T10:00:00.000000+00:00",
  "version": "1.0.0",
  "services": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "cache": {
      "status": "healthy",
      "message": "Cache is working"
    }
  },
  "system": {
    "django_version": "4.2.7",
    "python_version": "3.10.12",
    "debug_mode": true
  },
  "stats": {
    "users": 4,
    "vendors": 1,
    "items": 0,
    "categories": 0,
    "sales_backups": 0
  }
}
```

**Unhealthy Response (503):**
```json
{
  "status": "unhealthy",
  "timestamp": "2026-01-01T10:00:00.000000+00:00",
  "version": "1.0.0",
  "services": {
    "database": {
      "status": "unhealthy",
      "message": "Database connection failed: connection refused"
    }
  },
  "system": {
    "django_version": "4.2.7",
    "python_version": "3.10.12",
    "debug_mode": true
  }
}
```

**Example (cURL):**
```bash
curl http://localhost:8000/health/
```

**Use Cases:**
- Monitor server status
- Check database connectivity
- Load balancer health checks
- Mobile app connectivity verification
- System diagnostics

---

## Authentication

### Register New Vendor

**POST** `/auth/register`

**No authentication required**

Creates a new vendor account. The account will be **inactive** and require admin approval before login.

**Request Body:**
```json
{
  "username": "newvendor",
  "email": "newvendor@example.com",
  "password": "password123",
  "password_confirm": "password123",
  "business_name": "New Business Store",
  "phone": "+1234567890",
  "gst_no": "29NEWVENDOR1234F1Z5",
  "address": "123 Main St, City, State"
}
```

**Note:** This example uses a NEW username (`newvendor`). The test vendor `vendor1` already exists - use it for login examples, not registration.

**Field Descriptions:**
- `username`: Unique username for login (required)
- `email`: Valid email address (required, must be unique)
- `password`: Password (minimum 6 characters, required)
- `password_confirm`: Password confirmation (must match password, required)
- `business_name`: Name of the business/restaurant (required)
- `phone`: Phone number with country code (required)
- `gst_no`: GST number (GSTIN) (optional, can be omitted or set later via profile update. If provided, must be unique)
- `fssai_license`: FSSAI License Number (optional during registration, can be added later via admin)
- `address`: Business address (required)

**Note:** Billing mode (GST/Non-GST) is set per bill, not per vendor. Vendors can create both GST and Non-GST bills.

**Success Response (201):**
```json
{
  "message": "Registration successful. Your vendor account is pending approval. Please wait for admin approval.",
  "username": "newvendor",
  "business_name": "New Business Store",
  "status": "pending_approval"
}
```

**Error Response (400):**
```json
{
  "error": "Registration failed",
  "details": {
    "username": ["Username already exists."],
    "email": ["Email already registered."],
    "gst_no": ["GST number already registered."],
    "password": ["Passwords do not match."],
    "business_name": ["This field is required."],
    "phone": ["This field is required."],
    "address": ["This field is required."]
  }
}
```

**Note:** `gst_no` is optional. If provided, it must be unique. You can register without GST and add it later via profile update.

**Example 1: Registration with GST (cURL):**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newvendor",
    "email": "newvendor@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "business_name": "New Business Store",
    "phone": "+1234567890",
    "gst_no": "29NEWVENDOR1234F1Z5",
    "address": "123 Main St, City, State"
  }'
```

**Example 2: Registration without GST (cURL):**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newvendor2",
    "email": "newvendor2@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "business_name": "New Business Store 2",
    "phone": "+1234567891",
    "address": "124 Main St, City, State"
  }'
```

**Note:** Use a unique username. If providing GST number, it must be unique. The test vendor `vendor1` already exists - use it for login, not registration. Billing mode (GST/Non-GST) is set per bill, not during registration. GST number is optional and can be added later via `PATCH /auth/profile`.

---

### Login

**POST** `/auth/login`

**No authentication required**

Login to get an authentication token. Only approved vendors can login.
Both **vendor owners** and **vendor staff users** use this same endpoint.

**Token Permanence:** Tokens are **permanent and never expire automatically**. The same token is returned on each login (reused if it exists). Users stay logged in indefinitely unless they explicitly logout via `POST /auth/logout`.

**Request Body:**
```json
{
  "username": "vendor1",
  "password": "vendor123"
}
```

**Success Response (200) (Owner or Staff):**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "username": "vendor1",
  "message": "Login successful",
  "vendor": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "ABC Restaurant",
    "phone": "+919876543210",
    "fssai_license": "12345678901234",
    "logo_url": "https://bucket.s3.region.amazonaws.com/vendors/vendor-id/logo.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
    "footer_note": "Thank you for visiting!"
  }
}
```

**Notes:**

- The `vendor` object is included for **both** vendor owners and vendor staff users (all share the same vendor account).
- The `vendor` object contains:
- `logo_url`: Pre-signed URL to restaurant logo (temporary, expires in 1 hour) or null if not uploaded
- `fssai_license`: FSSAI License Number (required for restaurant bills)
- `footer_note`: Footer note to display on bills (optional)

Billing mode (GST/Non-GST) is set per bill when creating bills, not at vendor level.

**Error Responses:**

**Invalid Credentials (401):**
```json
{
  "error": "Invalid username or password. Please login.",
  "details": {...}
}
```

**Pending Approval (403):**
```json
{
  "error": "Your vendor account is pending approval. Please wait for admin approval.",
  "message": "Your vendor account has been created but is waiting for admin approval. You will be able to login once approved."
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "vendor1",
    "password": "vendor123"
  }'
```

---

### Logout

**POST** `/auth/logout`

**Requires authentication**

Invalidates the current authentication token.

**Headers:**
```
Authorization: Token <your_token>
```

**Success Response (200):**
```json
{
  "message": "Logout successful"
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

### Get Vendor Profile

**GET** `/auth/profile`

**Requires authentication**

Get vendor profile information including business details and logo.

**Headers:**
```
Authorization: Token <your_token>
```

**Success Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "vendor1",
  "email": "vendor@example.com",
  "business_name": "ABC Restaurant",
  "phone": "+1234567890",
  "address": "123 Main St, City",
  "gst_no": "29ABCDE1234F1Z5",
  "fssai_license": "12345678901234",
  "logo_url": "https://bucket.s3.region.amazonaws.com/vendors/.../logo.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
  "footer_note": "Thank you for visiting!",
  "bill_prefix": "INV",
  "bill_starting_number": 1,
  "last_bill_number": 42,
  "sac_code": "996331",
  "sac_gst_percentage": "5.00",
  "is_approved": true,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

**Field Descriptions:**
- `logo_url`: Pre-signed URL to restaurant logo (temporary, expires in 1 hour) or null if not uploaded
- `gst_no`: GST number (GSTIN) - can be null if not set. Can be updated via PATCH /auth/profile

**Example (cURL):**
```bash
curl -X GET http://localhost:8000/auth/profile \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

### Update Vendor Profile

**PATCH** `/auth/profile`

**Requires authentication**

Update vendor profile information including business details and logo upload.

**Headers:**
```
Authorization: Token <your_token>
Content-Type: application/json     (when updating text fields only)
// DO NOT set Content-Type for multipart/form-data - browser/axios will set it automatically with boundary
```

**Request Body (JSON - update business details only):**
```json
{
  "business_name": "Updated Restaurant Name",
  "phone": "+1234567890",
  "address": "Updated Address, City",
  "gst_no": "29UPDATED1234F1Z5",
  "fssai_license": "12345678901234",
  "footer_note": "Thank you for visiting!",
  "bill_prefix": "INV",
  "bill_starting_number": 100,
  "sac_code": "996331",
  "sac_gst_percentage": 5.00
}
```

**Request Body (multipart/form-data - with logo upload):**
```
business_name: Updated Restaurant Name
phone: +1234567890
address: Updated Address, City
fssai_license: 12345678901234
footer_note: Thank you for visiting!
bill_prefix: INV
bill_starting_number: 100
sac_code: 996331
sac_gst_percentage: 5.00
logo: <file>  (JPG, PNG, WebP)
```

**Field Descriptions:**
- All fields are optional (partial update supported)
- `logo`: Image file (JPG, PNG, WebP) - optional
- `gst_no`: GST number (GSTIN) - optional, can be set, updated, or cleared (set to empty string to clear). Must be unique if provided.
- `bill_prefix`: Prefix for bill numbers (e.g., "INV", "BILL", "REST"). Format: `{prefix}-{date}-{number}` (e.g., "INV-2026-01-27-0001")
- `bill_starting_number`: Starting bill number (to account for existing bills before system migration). **Can only be set once before any bills are created.** Cannot be changed after bills exist.
- `last_bill_number`: Read-only field showing the last generated bill number (auto-incremented by server)
- `sac_code`: SAC (Service Accounting Code) for vendor-level GST (e.g., "996331" for restaurant service). **If set, all items in bills use this SAC GST rate instead of their HSN codes.** Leave blank to use item-level HSN codes.
- `sac_gst_percentage`: GST percentage for SAC code (e.g., 5.00 for 5%). If SAC code is set but this is not set, default rate from mapping will be used.

**SAC Code (Service Accounting Code) - Vendor-Level GST:**
- SAC codes are used for **service-based businesses** like restaurants, hotels, catering services
- When `sac_code` is set on the vendor profile, **all items in bills use the SAC GST rate** (ignores item HSN codes)
- Common SAC codes:
  - `996331`: Restaurant service (dine-in/takeaway) - 5% GST
  - `996334`: Outdoor catering / Event catering - 5% or 18% GST (vendor must specify)
- Tax calculation with SAC:
  - Each item's tax = `item_subtotal × sac_gst_percentage / 100`
  - Total tax = sum of all item taxes
  - CGST = total_tax / 2, SGST = total_tax / 2 (for intra-state)
  - IGST = total_tax (for inter-state)
- **If SAC code is NOT set**, the system uses item-level HSN codes for tax calculation:
  - Each item uses its own `hsn_code` and `hsn_gst_percentage`
  - Different items can have different HSN codes and different GST rates
  - Tax calculated per item, then summed

**Success Response (200):**
```json
{
  "message": "Profile updated successfully",
  "vendor": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "vendor1",
    "email": "vendor@example.com",
    "business_name": "Updated Restaurant Name",
    "phone": "+1234567890",
    "address": "Updated Address, City",
    "fssai_license": "12345678901234",
    "logo_url": "https://bucket.s3.region.amazonaws.com/vendors/.../logo.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
    "footer_note": "Thank you for visiting!",
  "bill_prefix": "INV",
  "bill_starting_number": 100,
  "last_bill_number": 150,
  "sac_code": "996331",
  "sac_gst_percentage": "5.00",
  "is_approved": true,
    "created_at": "2026-01-01T10:00:00Z",
    "updated_at": "2026-01-01T10:05:00Z"
  }
}
```

**Error Response (400) - Changing bill_starting_number after bills exist:**
```json
{
  "error": "Cannot change bill_starting_number after bills have been created. Please contact admin if you need to reset bill numbering.",
  "details": {
    "bill_starting_number": ["Cannot change starting number after bills exist"]
  }
}
```

**Example 1: Update GST Number (cURL):**
```bash
curl -X PATCH http://localhost:8000/auth/profile \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "gst_no": "29NEWGST1234F1Z5"
  }'
```

**Example 2: Add GST Number (if not set during registration):**
```bash
curl -X PATCH http://localhost:8000/auth/profile \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "gst_no": "29ADDEDGST1234F1Z5"
  }'
```

**Example 3: Clear GST Number (set to empty):**
```bash
curl -X PATCH http://localhost:8000/auth/profile \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "gst_no": ""
  }'
```

**Note:** Empty string will be converted to `null`. GST number must be unique if provided.

**Example (cURL - update business details):**
```bash
curl -X PATCH http://localhost:8000/auth/profile \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Updated Restaurant Name",
    "phone": "+1234567890",
    "address": "Updated Address"
  }'
```

**Example (cURL - configure bill numbering):**
```bash
# Set bill prefix and starting number (one-time setup, before creating bills)
curl -X PATCH http://localhost:8000/auth/profile \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "bill_prefix": "INV",
    "bill_starting_number": 100
  }'
```

**Note:** 
- `bill_prefix` and `bill_starting_number` should be set **once** before creating bills
- `bill_starting_number` cannot be changed after bills have been created
- Server generates all bill numbers in format: `{prefix}-{date}-{number}` (e.g., "INV-2026-01-27-0100")
- All devices will receive server-generated bill numbers to ensure sequential numbering

**Example (cURL - upload logo):**
```bash
curl -X PATCH http://localhost:8000/auth/profile \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -F "business_name=Updated Restaurant Name" \
  -F "logo=@/path/to/logo.jpg"
```

**Example (JavaScript/Fetch - upload logo):**
```javascript
const formData = new FormData();
formData.append('business_name', 'Updated Restaurant Name');
formData.append('logo', logoFile); // File object from file input

const response = await fetch('http://localhost:8000/auth/profile', {
  method: 'PATCH',
  headers: {
    'Authorization': `Token ${token}`
  },
  body: formData
});

const data = await response.json();
console.log(data.vendor.logo_url); // Pre-signed URL for logo
```

---

### Forgot Password (Verify Username and Phone Number)

**POST** `/auth/forgot-password`

**No authentication required**

Verifies the username and phone number to initiate password reset flow. This is the first step in password reset.

🔐 **Important:**

- This flow is **only for the main vendor owner account** (the account created via `POST /auth/register`).
- **Staff users created by the vendor owner CANNOT use this forgot-password endpoint.**
- If a staff user forgets their password, the vendor owner must reset it using the **"Reset Staff Password"** endpoint (see below).

**Request Body:**
```json
{
  "username": "vendor1",
  "phone": "+919876543210"
}
```

**Field Descriptions:**
- `username`: Username of the **vendor owner** account (required)
- `phone`: Phone number of the vendor owner account (required, must match the username)

**Success Response (200):**
```json
{
  "message": "Username and phone number verified. You can now reset your password.",
  "username": "vendor1",
  "phone": "+919876543210",
  "business_name": "ABC Store"
}
```

**Error Responses:**
  
**Username Not Found (400):**
```json
{
  "error": "Username and phone number verification failed",
  "details": {
    "non_field_errors": ["Username not found. Please check and try again."]
  }
}
```

**Username and GST Don't Match (400):**
```json
{
  "error": "Username and phone number verification failed",
  "details": {
    "non_field_errors": ["Username and phone number do not match."]
  }
}
```

**Account Pending Approval (400):**
```json
{
  "error": "Username and phone number verification failed",
  "details": {
    "non_field_errors": ["Your vendor account is pending approval. Please contact admin."]
  }
}
```

**Account Inactive (400):**
```json
{
  "error": "Username and phone number verification failed",
  "details": {
    "non_field_errors": ["Your account is inactive. Please contact admin."]
  }
}
```

**Staff User (Non-Owner) Attempts Forgot Password (400):**

```json
{
  "error": "Username and phone number verification failed",
  "details": {
    "non_field_errors": [
      "Username does not belong to a vendor owner account. Please contact your vendor admin."
    ]
  }
}
```
```json
{
  "error": "Username and phone number verification failed",
  "details": {
    "non_field_errors": ["Your account is inactive. Please contact admin."]
  }
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"username": "vendor1", "phone": "+919876543210"}'
```

---

### Reset Password

**POST** `/auth/reset-password`

**No authentication required**

Resets the password for a **vendor owner** account using their username and phone number. This is the second step after verifying username and phone number.

🔐 **Important:**

- This endpoint only works for the **vendor owner** username.
- Staff users **cannot** reset their own passwords via this endpoint; the owner must reset it for them.

**Request Body:**
```json
{
  "username": "vendor1",
  "phone": "+919876543210",
  "new_password": "newpassword123",
  "new_password_confirm": "newpassword123"
}
```

**Field Descriptions:**
- `username`: Username of the **vendor owner** account (required, must match forgot-password step)
- `phone`: Phone number (required, must match the username and forgot-password step)
- `new_password`: New password (minimum 6 characters, required)
- `new_password_confirm`: Password confirmation (must match new_password, required)

**Success Response (200):**
```json
{
  "message": "Password reset successful. You can now login with your new password.",
  "username": "vendor1"
}
```

**Error Responses:**

**Passwords Don't Match (400):**
```json
{
  "error": "Password reset failed",
  "details": {
    "new_password": ["Passwords do not match."]
  }
}
```

**Username and Phone Don't Match (400):**
```json
{
  "error": "Password reset failed",
  "details": {
    "non_field_errors": ["Username and phone number do not match."]
  }
}
```

**Username Not Found (400):**
```json
{
  "error": "Password reset failed",
  "details": {
    "non_field_errors": ["Username not found."]
  }
}
```

**Account Issues (400):**
```json
{
  "error": "Password reset failed",
  "details": {
    "non_field_errors": ["Your vendor account is pending approval."]
  }
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "username": "vendor1",
    "phone": "+919876543210",
    "new_password": "newpassword123",
    "new_password_confirm": "newpassword123"
  }'
```

**Password Reset Flow:**
1. User forgets password
2. User enters username and phone number → `POST /auth/forgot-password`
3. System verifies username and phone number match and returns confirmation
4. User enters new password with username and phone → `POST /auth/reset-password`
5. Password is reset, all existing tokens are invalidated
6. User can now login with new password

**Staff User Flow (No Forgot-Password):**

1. Staff user forgets password.
2. Staff user contacts vendor owner.
3. Vendor owner calls `POST /auth/vendor/users/<user_id>/reset-password` to set a new password for the staff user.
4. Staff user logs in with the new password via `POST /auth/login`.

---

### Vendor Staff User Management (Multi-User per Vendor)

These endpoints allow the **vendor owner** to create and manage multiple staff users who share the same vendor account.

**🔒 Security PIN Required:** All sensitive operations (create staff, reset password, remove staff) require a **security PIN** that the owner sets. This adds an extra layer of security to prevent unauthorized access to user management features.

All staff users:
- Use the same `/auth/login` endpoint.
- Get the same `vendor` object in the response.
- Can perform all billing actions (items, bills, dashboard, etc.).
- **Cannot** manage other users or access Django Admin.

#### Security PIN Management

Before using staff management endpoints, the owner must set a security PIN:

**1. Set Security PIN**

**POST** `/auth/vendor/security-pin/set`

**Requires authentication** (vendor owner only)

Set or change the security PIN. PIN must be at least 4 characters.

**Headers:**

```
Authorization: Token <owner_token>
Content-Type: application/json
```

**Request Body (First Time - Set PIN):**

```json
{
  "pin": "1234",
  "pin_confirm": "1234"
}
```

**Request Body (Change Existing PIN):**

```json
{
  "old_pin": "1234",
  "pin": "5678",
  "pin_confirm": "5678"
}
```

**Success Response (200):**

```json
{
  "message": "Security PIN set successfully"
}
```

**Error Responses:**

- PIN too short (400): `{"error": "PIN must be at least 4 digits"}`
- PINs don't match (400): `{"error": "PIN and confirmation do not match"}`
- Invalid old PIN (403): `{"error": "Invalid old PIN"}` (when changing existing PIN)

**Request Example (cURL - Set PIN First Time):**
```bash
curl -X POST http://localhost:8000/auth/vendor/security-pin/set \
  -H "Authorization: Token YOUR_OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin": "1234",
    "pin_confirm": "1234"
  }'
```

**Request Example (cURL - Change Existing PIN):**
```bash
curl -X POST http://localhost:8000/auth/vendor/security-pin/set \
  -H "Authorization: Token YOUR_OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_pin": "1234",
    "pin": "5678",
    "pin_confirm": "5678"
  }'
```

**Request Example (JavaScript/Fetch):**
```javascript
const response = await fetch('http://localhost:8000/auth/vendor/security-pin/set', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${ownerToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    pin: '1234',
    pin_confirm: '1234'
  })
});

const result = await response.json();
console.log(result);
```

**2. Verify Security PIN**

**POST** `/auth/vendor/security-pin/verify`

**Requires authentication** (vendor owner only)

Verify the security PIN (for frontend to check before showing sensitive UI). This does not unlock anything permanently - it's just for UI validation.

**Headers:**

```
Authorization: Token <owner_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "pin": "1234"
}
```

**Success Response (200):**

```json
{
  "message": "Security PIN verified successfully",
  "verified": true
}
```

**Error Response (403):**

```json
{
  "error": "Invalid security PIN",
  "verified": false
}
```

**Request Example (cURL):**
```bash
curl -X POST http://localhost:8000/auth/vendor/security-pin/verify \
  -H "Authorization: Token YOUR_OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pin": "1234"
  }'
```

**Request Example (JavaScript/Fetch):**
```javascript
const response = await fetch('http://localhost:8000/auth/vendor/security-pin/verify', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${ownerToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    pin: '1234'
  })
});

const result = await response.json();
if (result.verified) {
  console.log('PIN verified - show sensitive UI');
} else {
  console.log('Invalid PIN');
}
```

**3. Check PIN Status**

**GET** `/auth/vendor/security-pin/status`

**Requires authentication** (vendor owner only)

Check if a security PIN is set (does not reveal the PIN).

**Headers:**

```
Authorization: Token <owner_token>
```

**Success Response (200):**

```json
{
  "has_pin": true
}
```

**Request Example (cURL):**
```bash
curl -X GET http://localhost:8000/auth/vendor/security-pin/status \
  -H "Authorization: Token YOUR_OWNER_TOKEN"
```

**Request Example (JavaScript/Fetch):**
```javascript
const response = await fetch('http://localhost:8000/auth/vendor/security-pin/status', {
  headers: {
    'Authorization': `Token ${ownerToken}`
  }
});

const result = await response.json();
if (result.has_pin) {
  console.log('PIN is set - show PIN input field');
} else {
  console.log('No PIN set - show PIN setup form');
}
```

---

#### 1. Create Staff User

**POST** `/auth/vendor/users/create`

**Requires authentication** (vendor owner only) + **Security PIN**

Creates a new staff user under the current vendor. The staff user can login and do billing, but cannot manage users.

**Headers:**

```
Authorization: Token <owner_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "username": "cashier1",
  "password": "cashier123",
  "email": "cashier1@example.com",
  "security_pin": "1234"
}
```

**Field Descriptions:**
- `username` (required, unique): Username for the staff user.
- `password` (required, min length 6): Initial password for the staff user.
- `email` (optional): Contact email for the staff user.
- `security_pin` (required): Security PIN to authorize this operation.

**Success Response (201):**

```json
{
  "message": "Staff user created successfully",
  "user": {
    "id": 7,
    "username": "cashier1",
    "email": "cashier1@example.com",
    "role": "staff",
    "created_at": "2026-01-27T12:00:00Z"
  }
}
```

**Error Responses:**

- Missing fields (400): `{"error": "Username and password are required"}`
- Username already exists (400): `{"error": "Username already exists"}`
- Not owner (403): `{"error": "Only vendor owner can create staff users"}`
- PIN required (400): `{"error": "Security PIN is required for this operation"}`
- Invalid PIN (403): `{"error": "Invalid security PIN"}`

**Request Example (cURL):**
```bash
curl -X POST http://localhost:8000/auth/vendor/users/create \
  -H "Authorization: Token YOUR_OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier1",
    "password": "cashier123",
    "email": "cashier1@example.com",
    "security_pin": "1234"
  }'
```

**Request Example (JavaScript/Fetch):**
```javascript
const response = await fetch('http://localhost:8000/auth/vendor/users/create', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${ownerToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'cashier1',
    password: 'cashier123',
    email: 'cashier1@example.com',
    security_pin: '1234'
  })
});

const result = await response.json();
console.log('Staff user created:', result.user);
```

#### 2. List Vendor Users (Owner + Staff)

**GET** `/auth/vendor/users`

**Requires authentication** (any vendor user)

Lists all active users (owner + staff) for the current vendor.

**Headers:**

```
Authorization: Token <vendor_token>
```

**Success Response (200):**

```json
{
  "users": [
    {
      "id": 3,
      "username": "vendor1",
      "email": "vendor1@example.com",
      "role": "owner",
      "created_at": "2026-01-01T10:00:00Z",
      "created_by": null
    },
    {
      "id": 7,
      "username": "cashier1",
      "email": "cashier1@example.com",
      "role": "staff",
      "created_at": "2026-01-27T12:00:00Z",
      "created_by": "vendor1"
    }
  ]
}
```

**Request Example (cURL):**
```bash
curl -X GET http://localhost:8000/auth/vendor/users \
  -H "Authorization: Token YOUR_VENDOR_TOKEN"
```

**Request Example (JavaScript/Fetch):**
```javascript
const response = await fetch('http://localhost:8000/auth/vendor/users', {
  headers: {
    'Authorization': `Token ${vendorToken}`
  }
});

const result = await response.json();
console.log('Vendor users:', result.users);
```

#### 3. Reset Staff Password (Owner Only)

**POST** `/auth/vendor/users/<user_id>/reset-password`

**Requires authentication** (vendor owner only) + **Security PIN**

Resets the password for a staff user. Staff cannot use forgot-password; only the owner can reset.

**Headers:**

```
Authorization: Token <owner_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "new_password": "newstaff123",
  "security_pin": "1234"
}
```

**Field Descriptions:**
- `new_password` (required): New password for the staff user.
- `security_pin` (required): Security PIN to authorize this operation.

**Success Response (200):**

```json
{
  "message": "Staff user password reset successfully"
}
```

**Error Responses:**

- Not owner (403): `{"error": "Only vendor owner can reset staff passwords"}`
- User not in this vendor (404): `{"error": "User not found in this vendor"}`
- Trying to reset owner password (400): `{"error": "Owner password must be reset via phone-based forgot-password flow."}`
- PIN required (400): `{"error": "Security PIN is required for this operation"}`
- Invalid PIN (403): `{"error": "Invalid security PIN"}`

**Request Example (cURL):**
```bash
curl -X POST http://localhost:8000/auth/vendor/users/7/reset-password \
  -H "Authorization: Token YOUR_OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "newstaff123",
    "security_pin": "1234"
  }'
```

**Request Example (JavaScript/Fetch):**
```javascript
const response = await fetch(`http://localhost:8000/auth/vendor/users/${staffUserId}/reset-password`, {
  method: 'POST',
  headers: {
    'Authorization': `Token ${ownerToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    new_password: 'newstaff123',
    security_pin: '1234'
  })
});

const result = await response.json();
console.log(result.message);
```

#### 4. Remove (Deactivate) Staff User (Owner Only)

**DELETE** `/auth/vendor/users/<user_id>`

**Requires authentication** (vendor owner only) + **Security PIN**

Deactivates a staff user. Marks both the `VendorUser` link and the underlying Django `User` as inactive and invalidates tokens.

**Headers:**

```
Authorization: Token <owner_token>
```

**Query Parameter or Request Body:**

**Option 1: Query Parameter (Recommended for DELETE):**
```
DELETE /auth/vendor/users/<user_id>?security_pin=1234
```

**Option 2: Request Body (JSON):**
```json
{
  "security_pin": "1234"
}
```

**Field Descriptions:**
- `security_pin` (required): Security PIN to authorize this operation. Can be provided via query parameter or request body.

**Success Response (200):**

```json
{
  "message": "Staff user removed successfully"
}
```

**Error Responses:**

- Not owner (403): `{"error": "Only vendor owner can remove staff users"}`
- User not in this vendor (404): `{"error": "User not found in this vendor"}`
- Attempt to remove owner (400): `{"error": "Cannot remove owner account"}`
- PIN required (400): `{"error": "Security PIN is required for this operation"}`
- Invalid PIN (403): `{"error": "Invalid security PIN"}`

**Request Example (cURL - Query Parameter):**
```bash
curl -X DELETE "http://localhost:8000/auth/vendor/users/7?security_pin=1234" \
  -H "Authorization: Token YOUR_OWNER_TOKEN"
```

**Request Example (cURL - Request Body):**
```bash
curl -X DELETE http://localhost:8000/auth/vendor/users/7 \
  -H "Authorization: Token YOUR_OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "security_pin": "1234"
  }'
```

**Request Example (JavaScript/Fetch - Query Parameter):**
```javascript
const response = await fetch(`http://localhost:8000/auth/vendor/users/${staffUserId}?security_pin=1234`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Token ${ownerToken}`
  }
});

const result = await response.json();
console.log(result.message);
```

**Request Example (JavaScript/Fetch - Request Body):**
```javascript
const response = await fetch(`http://localhost:8000/auth/vendor/users/${staffUserId}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Token ${ownerToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    security_pin: '1234'
  })
});

const result = await response.json();
console.log(result.message);
```

---

### Using Authentication Token

Include the token in the **Authorization** header for all authenticated requests:

```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Example (cURL):**
```bash
curl -X GET http://localhost:8000/items/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

**Example (JavaScript):**
```javascript
fetch('http://localhost:8000/items/', {
  headers: {
    'Authorization': `Token ${token}`
  }
})
```

---

## Vendor Registration & Approval

### Registration Flow

1. **Vendor registers** via `POST /auth/register`
   - **Required fields:** `username`, `email`, `password`, `password_confirm`, `business_name`, `phone`, `address`
   - **Optional fields:** `gst_no`, `fssai_license` (can be added later via profile update)
   - Creates User account (inactive)
   - Creates Vendor profile (not approved, GST number optional)
   - Returns: "Registration successful. Your account is pending approval."
   - **Note:** GST number is optional. If provided, must be unique. Phone number is required and will be used for password reset.

2. **Vendor tries to login** (before approval)
   - Returns 403: "Your vendor account is pending approval..."

3. **Sales Rep or Admin approves vendor**
   - **Option A:** Sales Rep Interface (Recommended)
     - Go to: `http://localhost:8000/sales-rep/`
     - Login with sales rep credentials
     - View vendors → Click "Approve" button
     - Mobile-friendly and easy to use
   - **Option B:** Django Admin Panel
     - Go to: `http://localhost:8000/admin/`
     - Navigate to: **Vendors** section
     - Select vendor(s) → Actions: "✓ Approve selected vendors" → Go
     - OR: Click vendor → Check "Approved" → Save

4. **Vendor can now login** and get token

### Sales Rep Interface - Approving Vendors

**Location:** `http://localhost:8000/sales-rep/`

**Default Credentials (created by setup.sh):**
- Username: `salesrep1`
- Password: `salesrep123`

**Features:**
- ✅ Mobile-responsive design (works on phones and tablets)
- ✅ Desktop-friendly interface
- ✅ View all vendors with approval and activation status
- ✅ **Approve/Reject vendors** - Controls approval status (`is_approved`)
- ✅ **Activate/Deactivate vendors** - Controls active status (`user.is_active`) - separate from approval
- ✅ Search and filter vendors (by approval status, active status, or search term)
- ✅ View detailed vendor information
- ✅ Statistics dashboard (pending/approved/active/inactive counts)

**How to Use:**
1. Login with sales rep credentials
2. View vendors and their status:
   - **Approval Status:** Pending or Approved (controls if vendor is approved)
   - **Active Status:** Active or Inactive (controls if vendor can login)
3. **Approve/Reject:** Click "Approve" or "Reject" to change approval status
4. **Activate/Deactivate:** Click "Activate" or "Deactivate" to change active status (separate from approval)
5. Filter by status: Pending Approval, Approved, Active, or Inactive
6. Or select multiple vendors and use "Bulk Approve"

**Important:**
- **Approval** and **Activation** are separate controls
- A vendor can be approved but inactive (cannot login)
- A vendor can be active but not approved (cannot use API)
- Both approval AND activation must be true for vendor to use the system

### Admin Panel - Approving Vendors

**Location:** `http://localhost:8000/admin/` → **Vendors**

**Features:**
- View all vendors with approval status
- Filter by "Approved: No" to see pending vendors
- Bulk approve: Select multiple → Actions → "Approve selected vendors"
- Individual approve: Click vendor → Check "Approved" → Save
- Search by business name, username, email, phone

---

## Categories

Categories organize items. **Each vendor can only create and use their own categories.** Categories are vendor-specific and isolated - vendors cannot see or use categories from other vendors.

### Get All Categories

**GET** `/items/categories/`

**Requires authentication + vendor approval**

Returns all categories created by the vendor (vendor-specific only).

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Drinks",
    "description": "Beverages and drinks",
    "is_active": true,
    "sort_order": 1,
    "item_count": 5,
    "created_at": "2026-01-01T10:00:00Z",
    "updated_at": "2026-01-01T10:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Breakfast",
    "description": "Morning meals",
    "is_active": true,
    "sort_order": 2,
    "item_count": 3,
    "created_at": "2026-01-01T10:00:00Z",
    "updated_at": "2026-01-01T10:00:00Z"
  }
]
```

---

### Create Category

**POST** `/items/categories/`

**Requires authentication + vendor approval**

Creates a new category for the vendor.

**Request Body:**
```json
{
  "name": "Lunch",
  "description": "Lunch items",
  "sort_order": 3
}
```

**Success Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Lunch",
  "description": "Lunch items",
  "is_active": true,
  "sort_order": 3,
  "item_count": 0,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

**Error Response (400):**
```json
{
  "name": ["Category with this name already exists for this vendor."]
}
```

---

### Get Category Details

**GET** `/items/categories/<uuid:id>`

**Requires authentication + vendor approval**

Returns details of a specific category.

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Drinks",
  "description": "Beverages and drinks",
  "is_active": true,
  "sort_order": 1,
  "item_count": 5,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

**Error Response (404):**
```json
{
  "error": "Category not found"
}
```

---

### Update Category

**PATCH** `/items/categories/<uuid:id>`

**Requires authentication + vendor approval**

Updates a category. Only vendor's own categories can be updated.

**Request Body (partial update):**
```json
{
  "name": "Beverages",
  "sort_order": 0
}
```

**Success Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Beverages",
  "description": "Beverages and drinks",
  "is_active": true,
  "sort_order": 0,
  "item_count": 5,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T11:00:00Z"
}
```

---

### Delete Category

**DELETE** `/items/categories/<uuid:id>`

**Requires authentication + vendor approval**

Deletes a category. Only vendor's own categories can be deleted.

**Success Response (204):**
```
No content
```

**Error Response (404):**
```json
{
  "error": "Category not found"
}
```

---

## Items

Items can belong to **multiple categories**. Create items first, then assign them to categories.

### Get All Items

**GET** `/items/`

**Requires authentication + vendor approval**

Returns all active items for the vendor.

**Query Parameters:**
- `category=<uuid>` - Filter items by category
- `search=<term>` - Search by name, description, SKU, or barcode

**Example:**
```
GET /items/?category=550e8400-e29b-41d4-a716-446655440000
GET /items/?search=coke
GET /items/?category=550e8400-e29b-41d4-a716-446655440000&search=cola
```

**Response (200):**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "vendor": "550e8400-e29b-41d4-a716-446655440010",
    "categories": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
    "category_ids": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
    "categories_list": [
      {"id": "550e8400-e29b-41d4-a716-446655440000", "name": "Drinks"},
      {"id": "550e8400-e29b-41d4-a716-446655440001", "name": "Breakfast"}
    ],
    "name": "Coca Cola",
    "description": "Cold drink",
    "price": "25.00",
    "stock_quantity": 100,
    "sku": "COKE-001",
    "barcode": "1234567890123",
    "is_active": true,
    "sort_order": 1,
    "vendor_name": "ABC Store",
    "image": null,
    "image_url": null,
    "last_updated": "2026-01-01T10:00:00Z",
    "created_at": "2026-01-01T10:00:00Z"
  }
]
```

---

### Create Item

**POST** `/items/`

**Requires authentication + vendor approval**

Creates a new item. Items can be assigned to multiple categories.

**Request Body:**
```json
{
  "name": "Coca Cola",
  "description": "Cold drink",
  "price": "25.00",
  "mrp_price": "25.00",
  "price_type": "exclusive",
  "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "stock_quantity": 100,
  "sku": "COKE-001",
  "barcode": "1234567890123",
  "category_ids": [
    "550e8400-e29b-41d4-a716-446655440000"
  ],
  "is_active": true,
  "sort_order": 1
}
```

**Field Descriptions:**
- `name`: Item name (required) - Shown clearly if no image uploaded
- `description`: Item description (optional)
- `price`: Base price (required)
- `mrp_price`: MRP Price - **MANDATORY** (Exclusive or Inclusive based on price_type)
- `price_type`: `"exclusive"` or `"inclusive"` (default: `"exclusive"`)
  - **Exclusive**: GST not included in MRP (GST added separately)
  - **Inclusive**: GST included in MRP (GST already in price)
- `hsn_code`: HSN (Harmonized System of Nomenclature) code (optional, e.g., "2106", "2202")
- `hsn_gst_percentage`: GST percentage for this HSN code (optional, e.g., 5.00 for 5%). Can override mapping defaults.
- `veg_nonveg`: `"veg"` or `"nonveg"` (optional)
- `category_ids`: Array of category UUIDs (must be vendor's own categories only)
- `image`: Item image file (optional - item name shown if no image)

**Note:** 
- `category_ids` is an array - items can belong to multiple categories!
- **Categories must belong to the vendor** - vendors can only use their own categories (vendor-specific, isolated)
- Image upload is optional - item names are shown clearly if no image
- GST percentage is not compulsory during item creation
- MRP price is MANDATORY for new items

**Success Response (201):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "vendor": "550e8400-e29b-41d4-a716-446655440010",
  "categories": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
  "category_ids": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
  "categories_list": [
    {"id": "550e8400-e29b-41d4-a716-446655440000", "name": "Drinks"},
    {"id": "550e8400-e29b-41d4-a716-446655440001", "name": "Breakfast"}
  ],
  "name": "Coca Cola",
  "description": "Cold drink",
  "price": "25.00",
  "mrp_price": "25.00",
  "price_type": "exclusive",
  "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "stock_quantity": 100,
  "sku": "COKE-001",
  "barcode": "1234567890123",
  "is_active": true,
  "sort_order": 1,
  "vendor_name": "ABC Restaurant",
  "image": null,
  "image_url": null,
  "last_updated": "2026-01-01T10:00:00Z",
  "created_at": "2026-01-01T10:00:00Z"
}
```

---

## Complete Item Creation Examples - All Cases

### Example 1: Item with 0% GST - Exclusive Pricing - Without Image - Veg

**Scenario:** Basic item with no GST, exclusive pricing, no image, vegetarian.

```json
{
  "name": "Rice",
  "description": "Plain rice",
  "price": "50.00",
  "mrp_price": "50.00",
  "price_type": "exclusive",
  "hsn_code": "2106",
  "hsn_gst_percentage": "0.00",
  "veg_nonveg": "veg",
  "stock_quantity": 100,
  "category_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/items/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rice",
    "price": "50.00",
    "mrp_price": "50.00",
    "price_type": "exclusive",
    "hsn_code": "2106",
    "hsn_gst_percentage": "0.00",
    "veg_nonveg": "veg",
    "category_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'
```

---

### Example 2: Item with 5% GST - Exclusive Pricing - Without Image - Veg

**Scenario:** Item with 5% GST, exclusive pricing.

```json
{
  "name": "Tea",
  "description": "Hot tea",
  "price": "20.00",
  "mrp_price": "20.00",
  "price_type": "exclusive",
  "hsn_code": "2106",
  "hsn_gst_percentage": "5.00",
  "veg_nonveg": "veg",
  "stock_quantity": 200,
  "category_ids": ["550e8400-e29b-41d4-a716-446655440001"]
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/items/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tea",
    "price": "20.00",
    "mrp_price": "20.00",
    "price_type": "exclusive",
    "hsn_code": "2106",
    "hsn_gst_percentage": "5.00",
    "veg_nonveg": "veg",
    "category_ids": ["550e8400-e29b-41d4-a716-446655440001"]
  }'
```

---

### Example 3: Item with 8% GST - Exclusive Pricing - Without Image - Veg

**Scenario:** Item with 8% GST, exclusive pricing.

```json
{
  "name": "Snacks",
  "description": "Mixed snacks",
  "price": "100.00",
  "mrp_price": "100.00",
  "price_type": "exclusive",
  "hsn_code": "2106",
  "hsn_gst_percentage": "12.00",
  "veg_nonveg": "veg",
  "stock_quantity": 50,
  "category_ids": ["550e8400-e29b-41d4-a716-446655440002"]
}
```

---

### Example 4: Item with 18% GST - Exclusive Pricing - Without Image - Veg

**Scenario:** Item with 18% GST, exclusive pricing.

```json
{
  "name": "Pizza Margherita",
  "description": "Classic pizza",
  "price": "200.00",
  "mrp_price": "200.00",
  "price_type": "exclusive",
  "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "stock_quantity": 30,
  "category_ids": ["550e8400-e29b-41d4-a716-446655440003"]
}
```

---

### Example 5: Item with Custom GST (12%) - Exclusive Pricing - Without Image - Veg

**Scenario:** Item with custom GST percentage (12%), exclusive pricing.

```json
{
  "name": "Special Dish",
  "description": "Custom GST item",
  "price": "150.00",
  "mrp_price": "150.00",
  "price_type": "exclusive",
  "hsn_code": "2106",
  "hsn_gst_percentage": "12.00",
  "veg_nonveg": "veg",
  "stock_quantity": 25,
  "category_ids": ["550e8400-e29b-41d4-a716-446655440004"]
}
```

**Note:** Custom GST percentages (any value between 0-100) are supported.

---

### Example 6: Item with 18% GST - Inclusive Pricing - Without Image - Veg

**Scenario:** Item with inclusive pricing (GST already included in MRP).

```json
{
  "name": "Pizza (Inclusive)",
  "description": "Pizza with GST included",
  "price": "200.00",
  "mrp_price": "236.00",
  "price_type": "inclusive",
  "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "stock_quantity": 30,
  "category_ids": ["550e8400-e29b-41d4-a716-446655440003"]
}
```

**Note:** For inclusive pricing, MRP already includes GST. When calculating bill, GST is extracted from MRP.

---

### Example 7: Item with 18% GST - Exclusive Pricing - With Image - Veg

**Scenario:** Item with image upload, exclusive pricing.

**cURL Example (with image):**
```bash
curl -X POST http://localhost:8000/items/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "name=Pizza Margherita" \
  -F "description=Classic pizza" \
  -F "price=200.00" \
  -F "mrp_price=200.00" \
  -F "price_type=exclusive" \
  -F "hsn_code=2105" \
  -F "hsn_gst_percentage=18.00" \
  -F "veg_nonveg=veg" \
  -F "stock_quantity=30" \
  -F "category_ids=[\"550e8400-e29b-41d4-a716-446655440003\"]" \
  -F "image=@/path/to/pizza.jpg"
```

**JavaScript Example (with image):**
```javascript
const formData = new FormData();
formData.append('name', 'Pizza Margherita');
formData.append('price', '200.00');
formData.append('mrp_price', '200.00');
formData.append('price_type', 'exclusive');
formData.append('hsn_code', '2105');
formData.append('hsn_gst_percentage', '18.00');
formData.append('veg_nonveg', 'veg');
formData.append('stock_quantity', '30');
formData.append('category_ids', JSON.stringify(['550e8400-e29b-41d4-a716-446655440003']));
formData.append('image', imageFile); // File object

const response = await fetch('http://localhost:8000/items/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`
  },
  body: formData
});

const item = await response.json();
// item.image_url contains pre-signed URL - download and cache immediately!
```

---

### Example 8: Item with 18% GST - Exclusive Pricing - Without Image - Non-Veg

**Scenario:** Non-vegetarian item, exclusive pricing.

```json
{
  "name": "Chicken Biryani",
  "description": "Spicy chicken biryani",
  "price": "250.00",
  "mrp_price": "250.00",
  "price_type": "exclusive",
  "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
  "veg_nonveg": "nonveg",
  "stock_quantity": 20,
  "category_ids": ["550e8400-e29b-41d4-a716-446655440005"]
}
```

---

### Example 9: Item Creation (No Discounts at Item Level)

**Note:** Item-level discounts have been removed. All discounts are now applied at the bill level using `discount_percentage` when creating bills.

**Item Example (Standard):**
```json
{
  "name": "Pizza",
  "description": "Classic pizza",
  "price": "200.00",
  "mrp_price": "200.00",
  "price_type": "exclusive",
  "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "stock_quantity": 30,
  "category_ids": ["550e8400-e29b-41d4-a716-446655440003"]
}
```

**To apply discounts:** Use `discount_percentage` when creating bills (see Bill Examples 8 and 16).

---

### Example 10: Item with Multiple Categories

**Scenario:** Item belongs to multiple categories (breakfast, lunch, dinner).

```json
{
  "name": "Combo Meal",
  "description": "Full combo meal",
  "price": "300.00",
  "mrp_price": "300.00",
  "price_type": "exclusive",
  "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "stock_quantity": 15,
  "category_ids": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002",
    "550e8400-e29b-41d4-a716-446655440003"
  ]
}
```

**Note:** Items can belong to multiple categories. Use array of category UUIDs.

---

### Example 11: Item with 0% GST - Inclusive Pricing - With Image - Non-Veg

**Scenario:** Non-veg item with 0% GST, inclusive pricing, with image.

**cURL Example:**
```bash
curl -X POST http://localhost:8000/items/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "name=Plain Rice" \
  -F "price=50.00" \
  -F "mrp_price=50.00" \
  -F "price_type=inclusive" \
  -F "gst_percentage=0.00" \
  -F "veg_nonveg=nonveg" \
  -F "stock_quantity=100" \
  -F "category_ids=[\"550e8400-e29b-41d4-a716-446655440000\"]" \
  -F "image=@/path/to/rice.jpg"
```

---

### Example 12: Item without GST Percentage (Optional Field)

**Scenario:** Item created without GST percentage (GST can be set later).

```json
{
  "name": "Water Bottle",
  "description": "Mineral water",
  "price": "20.00",
  "mrp_price": "20.00",
  "price_type": "exclusive",
  "veg_nonveg": "veg",
  "stock_quantity": 500,
  "category_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

**Note:** `hsn_code` and `hsn_gst_percentage` are optional during item creation. If not provided, items will have 0% GST. HSN codes can be updated later.

---

### GST Percentage Summary

**Supported GST Percentages:**
- `0.00` - 0% GST (exempt items like rice, wheat)
- `5.00` - 5% GST (items like tea, coffee)
- `8.00` - 8% GST (items like snacks)
- `18.00` - 18% GST (most restaurant items)
- **Custom values** - Any decimal value between 0-100 (e.g., 12.00, 28.00)

**Price Type Summary:**
- `"exclusive"` - GST not included in MRP (GST added separately during billing)
- `"inclusive"` - GST included in MRP (GST already in price, extracted during billing)

**Veg/Non-Veg Options:**
- `"veg"` - Vegetarian item
- `"nonveg"` - Non-vegetarian item
- `null` or omitted - Not specified

**Image Upload:**
- **Optional** - Items work fine without images
- **Supported formats:** JPG, JPEG, PNG, WebP
- **Use `multipart/form-data`** when uploading images
- **Response includes `image_url`** with pre-signed URL (expires in 1 hour)

---

### Upload Item Image

**POST** `/items/` (with image upload)

**Content-Type:** `multipart/form-data` (required when uploading images)

Items can include images. When uploading an image, use `multipart/form-data` instead of `application/json`.

**How it works:**
1. **You send the image file** to the server (multipart/form-data)
2. **Server uploads the image** to S3 (or local storage)
3. **Server returns a pre-signed URL** in the `image_url` field (for downloading/viewing the image)

**Important:**
- Image upload is **optional** - items work fine without images
- Supported formats: JPG, JPEG, PNG, WebP
- **You upload the image file directly** - no pre-signed URL needed for upload
- **After upload**, the response includes a **pre-signed URL** in `image_url` field (for downloading/viewing)
- Pre-signed URLs expire after 1 hour - download and cache images immediately

**Request Example (cURL):**
```bash
curl -X POST http://localhost:8000/items/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "name=Coca Cola" \
  -F "description=Cold drink" \
  -F "mrp_price=25.00" \
  -F "price_type=exclusive" \
  -F "hsn_code=2105" \
  -F "hsn_gst_percentage=18.00" \
  -F "veg_nonveg=veg" \
  -F "stock_quantity=100" \
  -F "category_ids=[\"550e8400-e29b-41d4-a716-446655440000\"]" \
  -F "image=@/path/to/image.jpg"
```

**Request Example (JavaScript/Fetch):**
```javascript
const formData = new FormData();
formData.append('name', 'Coca Cola');
formData.append('description', 'Cold drink');
formData.append('mrp_price', '25.00');
formData.append('price_type', 'exclusive');
formData.append('hsn_code', '2105');
formData.append('hsn_gst_percentage', '18.00');
formData.append('veg_nonveg', 'veg');
formData.append('stock_quantity', '100');
formData.append('category_ids', JSON.stringify(['550e8400-e29b-41d4-a716-446655440000']));
formData.append('image', imageFile); // File object from file input

const response = await fetch('http://localhost:8000/items/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`
    // Don't set Content-Type - browser will set it with boundary
  },
  body: formData
});

const item = await response.json();
console.log('Item created:', item);
console.log('Image URL (pre-signed):', item.image_url);
```

**Request Example (React Native):**
```javascript
import FormData from 'form-data';
import { Platform } from 'react-native';

const formData = new FormData();
formData.append('name', 'Coca Cola');
formData.append('mrp_price', '25.00');
formData.append('price_type', 'exclusive');
formData.append('hsn_code', '2105');
formData.append('hsn_gst_percentage', '18.00');
formData.append('image', {
  uri: Platform.OS === 'ios' ? imageUri.replace('file://', '') : imageUri,
  type: 'image/jpeg',
  name: 'item_image.jpg',
});

const response = await fetch('http://localhost:8000/items/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`
    // DO NOT set Content-Type manually - axios/fetch will set it with boundary automatically
  },
  body: formData,
});

const item = await response.json();
// item.image_url contains pre-signed URL - download and cache immediately!
```

**Success Response (201) with Image:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Coca Cola",
  "description": "Cold drink",
  "mrp_price": "25.00",
  "price_type": "exclusive",
  "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "stock_quantity": 100,
  "image": "items/660e8400-e29b-41d4-a716-446655440000/image.jpg",
  "image_url": "https://bucket.s3.region.amazonaws.com/items/660e8400-e29b-41d4-a716-446655440000/image.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&X-Amz-Credential=...&X-Amz-Signature=...",
  "created_at": "2026-01-01T10:00:00Z"
}
```

**Note:** 
- `image_url` is a **pre-signed URL** (temporary, expires in 1 hour)
- Download and cache the image immediately - don't store the URL long-term
- The image is automatically uploaded to S3 (if `USE_S3=True`) or local storage

---

### Update Item Image

**PATCH** `/items/<uuid:id>/` (with image upload)

You can update an item's image by sending a PATCH request with `multipart/form-data`.

**How it works:**
1. **You send the new image file** to the server (multipart/form-data)
2. **Server uploads the new image** to S3 (or local storage)
3. **Server returns a new pre-signed URL** in `image_url` field (for downloading/viewing)

**Request Example (cURL):**
```bash
curl -X PATCH http://localhost:8000/items/660e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "name=Updated Name" \
  -F "image=@/path/to/new_image.jpg"
```

**Request Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('name', 'Updated Item Name');
formData.append('image', newImageFile);

const response = await fetch(`http://localhost:8000/items/${itemId}/`, {
  method: 'PATCH',
  headers: {
    'Authorization': `Token ${token}`
  },
  body: formData
});

const updatedItem = await response.json();
// updatedItem.image_url contains new pre-signed URL
```

**Success Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Item Name",
  "image": "items/660e8400-e29b-41d4-a716-446655440000/image.jpg",
  "image_url": "https://bucket.s3.region.amazonaws.com/items/660e8400-e29b-41d4-a716-446655440000/image.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
  ...
}
```

---

**Error Response (400):**
```json
{
  "error": "One or more categories not found or do not belong to vendor"
}
```

---

### Get Item Details

**GET** `/items/<uuid:id>`

**Requires authentication + vendor approval**

Returns details of a specific item.

**Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "vendor": "550e8400-e29b-41d4-a716-446655440010",
  "categories": ["550e8400-e29b-41d4-a716-446655440000"],
  "category_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "categories_list": [
    {"id": "550e8400-e29b-41d4-a716-446655440000", "name": "Drinks"}
  ],
  "name": "Coca Cola",
  "description": "Cold drink",
  "price": "25.00",
  "mrp_price": "25.00",
  "price_type": "exclusive",
  "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "stock_quantity": 100,
  "sku": "COKE-001",
  "barcode": "1234567890123",
  "is_active": true,
  "sort_order": 1,
  "vendor_name": "ABC Restaurant",
  "image": "items/660e8400-e29b-41d4-a716-446655440000/660e8400-e29b-41d4-a716-446655440000.jpg",
  "image_url": "https://bucket.s3.region.amazonaws.com/items/660e8400-e29b-41d4-a716-446655440000/image.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
  "last_updated": "2026-01-01T10:00:00Z",
  "created_at": "2026-01-01T10:00:00Z"
}
```

**Error Response (404):**
```json
{
  "error": "Item not found"
}
```

---

### Update Item

**PATCH** `/items/<uuid:id>`

**Requires authentication + vendor approval**

Updates an item. Supports partial updates. Can update categories and images.

**Note:** To update an item's image, use `multipart/form-data` (see [Update Item Image](#update-item-image) section above). For other fields, you can use `application/json`.

**Request Body (JSON - for non-image updates):**
```json
{
  "price": "30.00",
  "mrp_price": "35.00",
  "stock_quantity": 150,
    "hsn_code": "2106",
    "hsn_gst_percentage": "5.00",
  "category_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440002"
  ]
}
```

**Request Body (multipart/form-data - for image updates):**
See [Update Item Image](#update-item-image) section above for complete examples.

**Success Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "vendor": "550e8400-e29b-41d4-a716-446655440010",
  "categories": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440002"],
  "category_ids": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440002"],
  "categories_list": [
    {"id": "550e8400-e29b-41d4-a716-446655440000", "name": "Drinks"},
    {"id": "550e8400-e29b-41d4-a716-446655440002", "name": "Lunch"}
  ],
  "name": "Coca Cola",
  "description": "Cold drink",
  "price": "30.00",
  "stock_quantity": 150,
  "sku": "COKE-001",
  "barcode": "1234567890123",
  "is_active": true,
  "sort_order": 1,
  "vendor_name": "ABC Store",
  "image": "items/660e8400-e29b-41d4-a716-446655440000/660e8400-e29b-41d4-a716-446655440000.jpg",
  "image_url": "https://bucket.s3.region.amazonaws.com/items/660e8400-e29b-41d4-a716-446655440000/image.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
  "last_updated": "2026-01-01T11:00:00Z",
  "created_at": "2026-01-01T10:00:00Z"
}
```

**Image Update (multipart/form-data):**

To update an item's image, use `multipart/form-data`:

```bash
curl -X PATCH http://localhost:8000/items/{item_id}/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "name=Updated Item Name" \
  -F "image=@/path/to/new_image.jpg"
```

**Important:** 
- ⚠️ **DO NOT manually set `Content-Type: multipart/form-data` header** - Browser/axios will automatically set it with the required boundary parameter. Setting it manually will break the upload.

**JavaScript/React Native Example:**
```javascript
const formData = new FormData();
formData.append('name', 'Updated Item Name');
formData.append('price', '30.00');

// Update image
formData.append('image', {
  uri: imageUri,
  type: 'image/jpeg',
  name: 'item.jpg'
});

const response = await fetch(`http://localhost:8000/items/${itemId}/`, {
  method: 'PATCH',
  headers: {
    'Authorization': `Token ${token}`
  },
  body: formData
});
```

---

### Delete Item

**DELETE** `/items/<uuid:id>`

**Requires authentication + vendor approval**

Deletes an item.

**Success Response (204):**
```
No content
```

**Error Response (404):**
```json
{
  "error": "Item not found"
}
```

---

### Update Item Status (Backward Compatibility)

**PATCH** `/items/<uuid:id>/status`

**Requires authentication + vendor approval**

Quick update for item status or stock quantity (kept for backward compatibility).

**Request Body:**
```json
{
  "is_active": false,
  "stock_quantity": 50
}
```

**Success Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Coca Cola",
  "is_active": false,
  "stock_quantity": 50,
  ...
}
```

---

## Inventory Management

**⚠️ Important:** Inventory items are for **raw materials** that vendors use to make their products. This is separate from the Items API which is for products that vendors sell.

All inventory endpoints require authentication and vendor approval.

### Get Available Unit Types

**GET** `/inventory/unit-types/`

**No authentication required**

Returns all available unit types for inventory items.

**Success Response (200):**
```json
[
  {"value": "kg", "label": "Kilogram (kg)"},
  {"value": "g", "label": "Gram (g)"},
  {"value": "L", "label": "Liter (L)"},
  {"value": "mL", "label": "Milliliter (mL)"},
  {"value": "pcs", "label": "Piece (pcs)"},
  {"value": "pkt", "label": "Packet (pkt)"},
  {"value": "box", "label": "Box (box)"},
  {"value": "carton", "label": "Carton (carton)"},
  {"value": "bag", "label": "Bag (bag)"},
  {"value": "bottle", "label": "Bottle (bottle)"},
  {"value": "can", "label": "Can (can)"},
  {"value": "dozen", "label": "Dozen (dozen)"},
  {"value": "m", "label": "Meter (m)"},
  {"value": "cm", "label": "Centimeter (cm)"},
  {"value": "sqm", "label": "Square Meter (sqm)"},
  {"value": "cum", "label": "Cubic Meter (cum)"}
]
```

---

### Get All Inventory Items

**GET** `/inventory/`

**Requires authentication + vendor approval**

Returns all inventory items (raw materials) for the authenticated vendor.

**Query Parameters:**
- `is_active` (optional): Filter by active status (`true`/`false`). Default: `true`
- `low_stock` (optional): Filter items with low stock (`true`). Default: `false`
- `search` (optional): Search by name, description, SKU, barcode, or supplier name
- `unit_type` (optional): Filter by unit type (e.g., `kg`, `L`, `pcs`)

**Success Response (200):**
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "name": "Wheat Flour",
    "quantity": "50.5",
    "unit_type": "kg",
    "unit_type_display": "Kilogram (kg)",
    "sku": "FLOUR-001",
    "is_active": true,
    "is_low_stock": false,
    "needs_reorder": false,
    "updated_at": "2026-01-01T10:00:00Z"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440001",
    "name": "Cooking Oil",
    "quantity": "2.5",
    "unit_type": "L",
    "unit_type_display": "Liter (L)",
    "sku": "OIL-001",
    "is_active": true,
    "is_low_stock": true,
    "needs_reorder": true,
    "updated_at": "2026-01-01T10:00:00Z"
  }
]
```

**Example (cURL):**
```bash
# Get all active inventory items
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/inventory/

# Get low stock items
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/inventory/?low_stock=true

# Search inventory
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/inventory/?search=flour
```

---

### Create Inventory Item

**POST** `/inventory/`

**Requires authentication + vendor approval**

Creates a new inventory item (raw material).

**Request Body:**
```json
{
  "name": "Wheat Flour",
  "description": "Premium quality wheat flour for baking",
  "quantity": "50.0",
  "unit_type": "kg",
  "sku": "FLOUR-001",
  "barcode": "1234567890123",
  "supplier_name": "ABC Suppliers",
  "supplier_contact": "+1234567890",
  "min_stock_level": "10.0",
  "reorder_quantity": "100.0",
  "is_active": true
}
```

**Required Fields:**
- `name`: Name of the raw material
- `quantity`: Current stock quantity (decimal, >= 0)
- `unit_type`: Unit of measurement (see unit types endpoint)

**Optional Fields:**
- `description`: Description
- `sku`: Stock Keeping Unit
- `barcode`: Barcode
- `supplier_name`: Supplier name
- `supplier_contact`: Supplier contact
- `min_stock_level`: Minimum stock level for alerts (decimal, >= 0)
- `reorder_quantity`: Recommended reorder quantity (decimal, >= 0)
- `is_active`: Active status (default: `true`)

**Success Response (201):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "vendor": "550e8400-e29b-41d4-a716-446655440010",
  "vendor_name": "ABC Store",
  "name": "Wheat Flour",
  "description": "Premium quality wheat flour for baking",
  "quantity": "50.0",
  "unit_type": "kg",
  "unit_type_display": "Kilogram (kg)",
  "sku": "FLOUR-001",
  "barcode": "1234567890123",
  "supplier_name": "ABC Suppliers",
  "supplier_contact": "+1234567890",
  "min_stock_level": "10.0",
  "reorder_quantity": "100.0",
  "is_active": true,
  "is_low_stock": false,
  "needs_reorder": false,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z",
  "last_restocked_at": null
}
```

**Error Response (400):**
```json
{
  "error": "Inventory item with name \"Wheat Flour\" already exists for your vendor account"
}
```

---

### Get Inventory Item Details

**GET** `/inventory/<uuid:id>/`

**Requires authentication + vendor approval**

Returns details of a specific inventory item.

**Success Response (200):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "vendor": "550e8400-e29b-41d4-a716-446655440010",
  "vendor_name": "ABC Store",
  "name": "Wheat Flour",
  "description": "Premium quality wheat flour for baking",
  "quantity": "50.0",
  "unit_type": "kg",
  "unit_type_display": "Kilogram (kg)",
  "sku": "FLOUR-001",
  "barcode": "1234567890123",
  "supplier_name": "ABC Suppliers",
  "supplier_contact": "+1234567890",
  "min_stock_level": "10.0",
  "reorder_quantity": "100.0",
  "is_active": true,
  "is_low_stock": false,
  "needs_reorder": false,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z",
  "last_restocked_at": null
}
```

---

### Update Inventory Item

**PATCH** `/inventory/<uuid:id>/`

**Requires authentication + vendor approval**

Updates an inventory item. Supports partial updates.

**Request Body (partial update):**
```json
{
  "description": "Updated description",
  "min_stock_level": "15.0",
  "supplier_name": "New Supplier"
}
```

**Success Response (200):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  ...
  "description": "Updated description",
  "min_stock_level": "15.0",
  "supplier_name": "New Supplier",
  ...
}
```

---

### Update Inventory Stock

**PATCH** `/inventory/<uuid:id>/stock/`

**Requires authentication + vendor approval**

Updates stock quantity with different actions: set, add, or subtract.

**Request Body:**
```json
{
  "action": "add",
  "quantity": "10.0",
  "notes": "Received new shipment"
}
```

**Action Types:**
- `set`: Set exact quantity (default)
- `add`: Add to current quantity
- `subtract`: Subtract from current quantity

**Success Response (200):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  ...
  "quantity": "60.0",
  "last_restocked_at": "2026-01-01T11:00:00Z",
  ...
}
```

**Error Response (400):**
```json
{
  "error": "Cannot subtract more than current quantity"
}
```

**Example (cURL):**
```bash
# Add stock
curl -X PATCH \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "add", "quantity": "10.0", "notes": "New shipment"}' \
  http://localhost:8000/inventory/770e8400-e29b-41d4-a716-446655440000/stock/

# Subtract stock
curl -X PATCH \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "subtract", "quantity": "5.0"}' \
  http://localhost:8000/inventory/770e8400-e29b-41d4-a716-446655440000/stock/

# Set exact quantity
curl -X PATCH \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "set", "quantity": "100.0"}' \
  http://localhost:8000/inventory/770e8400-e29b-41d4-a716-446655440000/stock/
```

---

### Delete Inventory Item

**DELETE** `/inventory/<uuid:id>/`

**Requires authentication + vendor approval**

Deletes an inventory item.

**Success Response (204):**
No content

**Error Response (404):**
```json
{
  "error": "Inventory item not found"
}
```

---

## Complete Sync Architecture (Bi-Directional)

### Overview

The system supports **bi-directional sync** for offline-first mobile apps with multiple users and multiple devices per vendor:

- **Reverse Sync (Server → Mobile):** Download existing data from server
- **Forward Sync (Mobile → Server):** Upload changes made offline to server
- **Multi-User Support:** Owner + Staff users all sync same vendor data
- **Multi-Device Support:** Multiple devices per user can sync simultaneously

### Sync Flow Diagram

```mermaid
graph TB
    subgraph "Mobile Device 1 (Owner)"
        MD1[Mobile App]
        LDB1[(Local SQLite)]
        MD1 -->|1. Save Locally| LDB1
        LDB1 -->|2. Queue Changes| MD1
    end
    
    subgraph "Mobile Device 2 (Staff)"
        MD2[Mobile App]
        LDB2[(Local SQLite)]
        MD2 -->|1. Save Locally| LDB2
        LDB2 -->|2. Queue Changes| MD2
    end
    
    subgraph "Backend Server"
        API[API Endpoints]
        SDB[(PostgreSQL)]
        API -->|Store| SDB
        SDB -->|Query| API
    end
    
    MD1 -->|Reverse Sync: GET| API
    MD2 -->|Reverse Sync: GET| API
    API -->|Download Data| MD1
    API -->|Download Data| MD2
    
    MD1 -->|Forward Sync: POST| API
    MD2 -->|Forward Sync: POST| API
    API -->|Store Changes| SDB
    
    style MD1 fill:#e1f5ff
    style MD2 fill:#e1f5ff
    style LDB1 fill:#e1f5ff
    style LDB2 fill:#e1f5ff
    style API fill:#fff4e1
    style SDB fill:#e8f5e9
```

### Reverse Sync (Server → Mobile) - Download Data

**Purpose:** Mobile app downloads existing data from server (initial sync, new device, refresh)

**Endpoints:**
- `GET /items/categories/` - Download all categories
- `GET /items/` - Download all items
- `GET /backup/sync` - Download all bills (with incremental support)

**When to Use:**
- App startup (initial sync)
- New device login
- App needs fresh data
- After forward sync (to get updates from other devices)

**Multi-User Support:**
- ✅ Owner user can download vendor data
- ✅ Staff users can download **same vendor data** (all users under same vendor see same items/categories/bills)
- ✅ Multiple devices per user can all sync simultaneously

**Example Flow:**
```mermaid
sequenceDiagram
    participant Device1 as Device 1 (Owner)
    participant Device2 as Device 2 (Staff)
    participant Server as Backend Server
    participant DB as PostgreSQL
    
    Note over Device1,Device2: Both users under same vendor
    
    Device1->>Server: GET /items/categories/
    Server->>DB: Query categories
    DB-->>Server: All categories
    Server-->>Device1: 10 categories
    
    Device2->>Server: GET /items/categories/
    Server->>DB: Query categories
    DB-->>Server: All categories
    Server-->>Device2: 10 categories (SAME)
    
    Device1->>Server: GET /items/
    Server->>DB: Query items
    DB-->>Server: All items
    Server-->>Device1: 50 items
    
    Device2->>Server: GET /items/
    Server->>DB: Query items
    DB-->>Server: All items
    Server-->>Device2: 50 items (SAME)
    
    Device1->>Server: GET /backup/sync
    Server->>DB: Query bills
    DB-->>Server: All bills
    Server-->>Device1: 100 bills
    
    Device2->>Server: GET /backup/sync
    Server->>DB: Query bills
    DB-->>Server: All bills
    Server-->>Device2: 100 bills (SAME)
```

### Forward Sync (Mobile → Server) - Upload Changes

**Purpose:** Mobile app uploads changes made offline to server

**Endpoints:**
- `POST /items/categories/sync` - Upload category changes (create/update/delete)
- `POST /items/sync` - Upload item changes (create/update/delete)
- `POST /backup/sync` - Upload existing bills for syncing between devices

**When to Use:**
- After offline operations (create/edit/delete items)
- For syncing existing bills between devices
- Background sync when online
- User made changes while offline

**Conflict Resolution:**
- **Last-Write-Wins:** If server version is newer (by timestamp), server wins
- **Duplicate Bills:** Skipped automatically (by `invoice_number`)
- **Multiple Devices:** All devices can sync simultaneously (server handles it)

**Example Flow:**
```mermaid
sequenceDiagram
    participant Device1 as Device 1 (Owner)
    participant Device2 as Device 2 (Staff)
    participant Server as Backend Server
    participant DB as PostgreSQL
    
    Note over Device1: Offline: Creates 3 items
    Device1->>Device1: Save to local SQLite
    Device1->>Device1: Queue for sync
    
    Note over Device2: Offline: Creates 2 bills (via POST /bills/ when online)
    Device2->>Device2: Save to local SQLite
    Device2->>Device2: Queue for sync
    
    Note over Device1,Device2: Both come online
    
    Device1->>Server: POST /items/sync [3 items]
    Server->>DB: Save items
    DB-->>Server: Items saved
    Server-->>Device1: Confirmation
    
    Device2->>Server: POST /backup/sync [2 bills]
    Server->>DB: Save bills
    DB-->>Server: Bills saved
    Server-->>Device2: Confirmation
    
    Note over Device1,Device2: Both devices now have all data
    Device1->>Server: GET /backup/sync (get Device2's bills)
    Server-->>Device1: 2 new bills
    
    Device2->>Server: GET /items/ (get Device1's items)
    Server-->>Device2: 3 new items
```

### Complete Sync Scenarios

#### Scenario 1: Initial Sync (New Device)

```mermaid
graph LR
    A[App Starts] --> B[Login]
    B --> C[GET /items/categories/]
    C --> D[GET /items/]
    D --> E[GET /backup/sync]
    E --> F[Save to Local DB]
    F --> G[App Ready]
    
    style A fill:#e1f5ff
    style G fill:#c8e6c9
```

**Steps:**
1. User logs in → Get token
2. `GET /items/categories/` → Download all categories
3. `GET /items/` → Download all items (with category links)
4. `GET /backup/sync` → Download all bills
5. Save everything to local SQLite
6. App is ready to use

#### Scenario 2: Offline Operations + Sync

```mermaid
graph LR
    A[User Offline] --> B[Create Items]
    B --> C[Create Bills]
    C --> D[Save Locally]
    D --> E[Queue for Sync]
    E --> F[App Online]
    F --> G[POST /items/sync]
    G --> H[POST /backup/sync]
    H --> I[Mark as Synced]
    
    style A fill:#fff3e0
    style F fill:#e1f5ff
    style I fill:#c8e6c9
```

#### Scenario 3: Multiple Devices, Same User

```mermaid
graph TB
    subgraph "User: vendor1"
        D1[Device 1: Phone]
        D2[Device 2: Tablet]
    end
    
    D1 -->|Creates Item| S[Server]
    D2 -->|Downloads Item| S
    S -->|Syncs| D2
    
    D2 -->|Creates Bill| S
    D1 -->|Downloads Bill| S
    S -->|Syncs| D1
    
    style D1 fill:#e1f5ff
    style D2 fill:#e1f5ff
    style S fill:#fff4e1
```

#### Scenario 4: Multiple Users, Same Vendor

```mermaid
graph TB
    subgraph "Vendor: ABC Restaurant"
        U1[Owner: vendor1]
        U2[Staff: cashier1]
        U3[Staff: waiter1]
    end
    
    U1 -->|Creates Item| S[Server]
    U2 -->|Downloads Item| S
    U3 -->|Downloads Item| S
    
    U2 -->|Creates Bill| S
    U1 -->|Downloads Bill| S
    U3 -->|Downloads Bill| S
    
    style U1 fill:#e1f5ff
    style U2 fill:#e1f5ff
    style U3 fill:#e1f5ff
    style S fill:#fff4e1
```

---

## Reverse Sync Endpoints (Server → Mobile)

### Download All Categories

**GET** `/items/categories/`

**Requires authentication + vendor approval**

Downloads all categories created by the vendor (vendor-specific only). Used for initial sync and refreshing category list.

**Works for:** Owner + Staff users (all users under same vendor see same categories)

**Success Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Breakfast",
    "description": "Morning meals",
    "is_active": true,
    "sort_order": 1,
    "item_count": 15,
    "created_at": "2026-01-01T10:00:00Z",
    "updated_at": "2026-01-27T12:00:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Lunch",
    "description": "Afternoon meals",
    "is_active": true,
    "sort_order": 2,
    "item_count": 20,
    "created_at": "2026-01-01T10:00:00Z",
    "updated_at": "2026-01-27T12:00:00Z"
  }
]
```

**Request Example (cURL):**
```bash
curl -X GET http://localhost:8000/items/categories/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Request Example (JavaScript/Fetch):**
```javascript
const response = await fetch('http://localhost:8000/items/categories/', {
  headers: {
    'Authorization': `Token ${token}`
  }
});

const categories = await response.json();
console.log(`Downloaded ${categories.length} categories`);
// Save to local SQLite database
await saveCategoriesToLocalDB(categories);
```

**Note:** 
- Returns all active categories created by the vendor (vendor-specific only)
- Categories are needed before creating items (items reference categories by UUID)
- All users (owner + staff) under same vendor get same categories
- Each vendor can only use their own categories when creating items

---

### Download All Items

**GET** `/items/`

**Requires authentication + vendor approval**

Downloads all items for the vendor. Used for initial sync and refreshing item list.

**Works for:** Owner + Staff users (all users under same vendor see same items)

**Query Parameters:**
- `category=<uuid>` (optional) - Filter items by category
- `search=<term>` (optional) - Search items by name, description, SKU, barcode
- `is_active=<true|false>` (optional) - Filter by active status

**Success Response (200):**
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "name": "Pizza Margherita",
    "description": "Classic pizza",
    "price": "200.00",
    "mrp_price": "236.00",
    "price_type": "exclusive",
    "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
    "veg_nonveg": "veg",
    "categories": ["550e8400-e29b-41d4-a716-446655440000"],
    "category_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    "categories_list": [
      {"id": "550e8400-e29b-41d4-a716-446655440000", "name": "Lunch"}
    ],
    "image_url": "https://bucket.s3.region.amazonaws.com/items/.../image.jpg?X-Amz-Algorithm=...",
    "stock_quantity": 50,
    "is_active": true,
    "created_at": "2026-01-01T10:00:00Z",
    "last_updated": "2026-01-27T12:00:00Z"
  }
]
```

**Request Example (cURL):**
```bash
# Download all items
curl -X GET http://localhost:8000/items/ \
  -H "Authorization: Token YOUR_TOKEN"

# Filter by category
curl -X GET "http://localhost:8000/items/?category=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Token YOUR_TOKEN"

# Search items
curl -X GET "http://localhost:8000/items/?search=pizza" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Request Example (JavaScript/Fetch):**
```javascript
// Download all items
const response = await fetch('http://localhost:8000/items/', {
  headers: {
    'Authorization': `Token ${token}`
  }
});

const items = await response.json();
console.log(`Downloaded ${items.length} items`);

// Save to local SQLite database
await saveItemsToLocalDB(items);

// Download item images (pre-signed URLs expire after 1 hour!)
for (const item of items) {
  if (item.image_url) {
    await downloadAndCacheImage(item.image_url, item.id);
  }
}
```

**Important Notes:**
- Items include `category_ids` array (UUIDs of categories)
- Items include `categories_list` array (category names for display)
- `image_url` is pre-signed URL (expires after 1 hour) - download and cache immediately!
- All users (owner + staff) under same vendor get same items

---

### Download All Bills

**GET** `/backup/sync`

**Requires authentication + vendor approval**

Downloads bills from server. Supports incremental sync with `since` parameter.

**Works for:** Owner + Staff users (all users under same vendor see same bills)

**Query Parameters:**
- `since` (optional): ISO timestamp - Only get bills synced after this time (e.g., `2026-01-27T10:00:00Z`)
- `limit` (optional, default=1000): Maximum number of bills to return
- `billing_mode` (optional): Filter by billing mode (`gst` or `non_gst`)
- `start_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2026-01-01`)
- `end_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2026-01-31`)

**Success Response (200):**
```json
{
  "count": 2,
  "bills": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "invoice_number": "INV-2026-01-27-0001",
      "bill_number": "BN-001",
      "bill_date": "2026-01-27",
      "billing_mode": "gst",
      "items": [
        {
          "id": "990e8400-e29b-41d4-a716-446655440000",
          "item_name": "Pizza",
          "price": "200.00",
          "quantity": "2.00",
          "subtotal": "400.00",
          "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
          "item_gst_amount": "72.00"
        }
      ],
      "subtotal": "400.00",
      "cgst_amount": "36.00",
      "sgst_amount": "36.00",
      "total_tax": "72.00",
      "total_amount": "472.00",
      "payment_mode": "cash",
      "created_at": "2026-01-27T10:00:00Z"
    }
  ],
  "vendor_id": "aa0e8400-e29b-41d4-a716-446655440000",
  "vendor_name": "ABC Restaurant"
}
```

**Request Example (cURL - Full Sync):**
```bash
# Download all bills
curl -X GET http://localhost:8000/backup/sync \
  -H "Authorization: Token YOUR_TOKEN"
```

**Request Example (cURL - Incremental Sync):**
```bash
# Download only bills synced after timestamp (efficient for multiple devices)
curl -X GET "http://localhost:8000/backup/sync?since=2026-01-27T10:00:00Z" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Request Example (JavaScript/Fetch - Incremental Sync):**
```javascript
// Get last sync timestamp from local DB
const lastSyncTime = await getLastSyncTimestamp();

// Download only new bills since last sync
const response = await fetch(
  `http://localhost:8000/backup/sync?since=${lastSyncTime}`,
  {
    headers: {
      'Authorization': `Token ${token}`
    }
  }
);

const data = await response.json();
const bills = data.bills || [];

console.log(`Downloaded ${bills.length} new bills`);

// Save to local SQLite
await saveBillsToLocalDB(bills);

// Update last sync timestamp
await updateLastSyncTimestamp(new Date().toISOString());
```

**Important Notes:**
- Use `since` parameter for incremental sync (only get new bills)
- Without `since`, downloads all bills (use for initial sync only)
- All users (owner + staff) under same vendor get same bills
- Bills include nested `items` array with all bill items

---

## Forward Sync Endpoints (Mobile → Server)

### Sync Categories

**POST** `/items/categories/sync`

**Requires authentication + vendor approval**

Batch sync categories for offline-first mobile apps. Supports create, update, and delete operations with Last-Write-Wins conflict resolution.

**Request Body:**
```json
[
  {
    "operation": "create",
    "data": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "New Category",
      "description": "Category description",
      "sort_order": 1,
      "is_active": true
    },
    "timestamp": "2026-01-01T10:00:00Z"
  },
  {
    "operation": "update",
    "data": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Updated Category"
    },
    "timestamp": "2026-01-01T11:00:00Z"
  },
  {
    "operation": "delete",
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "timestamp": "2026-01-01T12:00:00Z"
  }
]
```

**Success Response (200):**
```json
{
  "synced": 3,
  "created": 1,
  "updated": 1,
  "deleted": 1,
  "categories": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "New Category",
      ...
    },
    ...
  ]
}
```

**Note:** Last-Write-Wins logic: If server has a newer timestamp, server data is kept. If client has a newer timestamp, client data is applied.

---

### Sync Items

**POST** `/items/sync`

**Requires authentication + vendor approval**

Batch sync items for offline-first mobile apps. Supports create, update, and delete operations with Last-Write-Wins conflict resolution.

**Request Body:**
```json
[
  {
    "operation": "create",
    "data": {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "name": "New Item",
      "price": "25.00",
      "stock_quantity": 100,
      "category_ids": ["550e8400-e29b-41d4-a716-446655440000"]
    },
    "timestamp": "2026-01-01T10:00:00Z"
  },
  {
    "operation": "update",
    "data": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "price": "30.00",
      "stock_quantity": 150
    },
    "timestamp": "2026-01-01T11:00:00Z"
  },
  {
    "operation": "delete",
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "timestamp": "2026-01-01T12:00:00Z"
  }
]
```

**Success Response (200):**
```json
{
  "synced": 3,
  "created": 1,
  "updated": 1,
  "deleted": 1,
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "name": "New Item",
      "image_url": "https://bucket.s3.region.amazonaws.com/items/.../image.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
      ...
    },
    ...
  ]
}
```

**Note:** 
- Last-Write-Wins logic: If server has a newer timestamp, server data is kept. If client has a newer timestamp, client data is applied.
- Images are not synced in batch sync - use regular POST/PATCH endpoints for image uploads.

---

## Bills (Direct CRUD Operations)

**Purpose:** Direct bill creation, update, and management operations. Use these endpoints when you want to create or modify bills directly on the server.

**Note:** For syncing existing bills between devices, use `/backup/sync` endpoints. To create new bills, use `/bills/` endpoints. See [Sales Backup (Multi-Device Sync Only)](#sales-backup-multi-device-sync-only) section.

### List Bills

**GET** `/bills/`

**Requires authentication + vendor approval**

List all bills for the vendor with filtering and pagination support.

**Query Parameters:**
- `billing_mode` (optional): Filter by billing mode (`gst` or `non_gst`)
- `start_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2026-01-01`)
- `end_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2026-01-31`)
- `payment_mode` (optional): Filter by payment mode (`cash`, `upi`, `card`, `credit`, `other`)
- `limit` (optional, default=100): Maximum number of bills to return
- `offset` (optional, default=0): Number of bills to skip (for pagination)

**Success Response (200):**
```json
{
  "count": 2,
  "total": 150,
  "offset": 0,
  "limit": 100,
  "bills": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "invoice_number": "INV-2026-01-27-0001",
      "bill_number": "BN-001",
      "bill_date": "2026-01-27",
      "billing_mode": "gst",
      "total_amount": "236.00",
      "item_count": 1,
      "payment_mode": "cash",
      "vendor_name": "ABC Restaurant",
      "created_at": "2026-01-27T10:00:00Z",
      "synced_at": "2026-01-27T10:00:00Z"
    }
  ]
}
```

**Example (cURL):**
```bash
# Get all bills
curl -X GET http://localhost:8000/bills/ \
  -H "Authorization: Token YOUR_TOKEN"

# Filter by billing mode
curl -X GET "http://localhost:8000/bills/?billing_mode=gst" \
  -H "Authorization: Token YOUR_TOKEN"

# Filter by date range
curl -X GET "http://localhost:8000/bills/?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Token YOUR_TOKEN"

# Pagination
curl -X GET "http://localhost:8000/bills/?limit=50&offset=100" \
  -H "Authorization: Token YOUR_TOKEN"
```

---

### Create Bill

**POST** `/bills/`

**Requires authentication + vendor approval**

Create a new bill directly on the server. **Invoice number is always auto-generated by the server** to ensure sequential numbering across all devices.

**Important:** 
- Server generates invoice number in format: `{prefix}-{date}-{number}` (e.g., "INV-2026-01-27-0001")
- Client cannot provide `invoice_number` - it will be ignored
- Server returns the generated invoice number in the response
- All devices receive sequential numbers from the server

**Request Body:**
```json
{
  "bill_date": "2026-01-27",
  "billing_mode": "gst",
  "items_data": [
    {
      "item_id": "item-uuid-1",
      "item_name": "Pizza Margherita",
      "price": "200.00",
      "mrp_price": "200.00",
      "price_type": "exclusive",
      "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
      "quantity": "2",
      "subtotal": "400.00",
      "item_gst_amount": "72.00",
      "veg_nonveg": "veg"
    }
  ],
  "subtotal": "400.00",
  "cgst_amount": "36.00",
  "sgst_amount": "36.00",
  "igst_amount": "0.00",
  "total_tax": "72.00",
  "total_amount": "472.00",
  "payment_mode": "cash",
  "amount_paid": "472.00",
  "customer_name": "John Doe",
  "customer_phone": "+91-9876543210"
}
```

**Field Descriptions:**
- `bill_date` (optional): Bill date (YYYY-MM-DD), defaults to today
- `billing_mode` (required): `"gst"` or `"non_gst"`
- `items_data` (required): Array of bill items
- `invoice_number` (ignored): Server always generates this - do not provide
- All other fields are optional

**Success Response (201):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "invoice_number": "INV-2026-01-27-0001",
  "bill_number": "INV-0001",
  "bill_date": "2026-01-27",
  "billing_mode": "gst",
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "item_name": "Pizza Margherita",
      "price": "200.00",
      "quantity": "2.00",
      "subtotal": "400.00",
      "item_gst_amount": "72.00"
    }
  ],
  "subtotal": "400.00",
  "total_amount": "472.00",
  "payment_mode": "cash",
  "created_at": "2026-01-27T10:00:00Z"
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/bills/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "billing_mode": "gst",
    "bill_date": "2026-01-27",
    "items_data": [
      {
        "item_name": "Pizza",
        "price": "200.00",
        "mrp_price": "200.00",
        "quantity": "2",
        "hsn_code": "2105",
        "hsn_gst_percentage": "18.00"
      }
    ],
    "subtotal": "400.00",
    "total_amount": "472.00",
    "payment_mode": "cash"
  }'
```

---

### Get Bill Details

**GET** `/bills/<uuid:id>/`

**Requires authentication + vendor approval**

Get detailed information about a specific bill including all items.

**Success Response (200):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "invoice_number": "INV-2026-01-27-0001",
  "bill_date": "2026-01-27",
  "billing_mode": "gst",
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "item_name": "Pizza Margherita",
      "price": "200.00",
      "mrp_price": "200.00",
      "quantity": "2.00",
      "subtotal": "400.00",
      "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
      "item_gst_amount": "72.00"
    }
  ],
  "subtotal": "400.00",
  "total_amount": "472.00",
  "payment_mode": "cash",
  "created_at": "2026-01-27T10:00:00Z"
}
```

**Example (cURL):**
```bash
curl -X GET http://localhost:8000/bills/880e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Token YOUR_TOKEN"
```

---

### Update Bill

**PATCH** `/bills/<uuid:id>/`

**Requires authentication + vendor approval**

Update an existing bill. Can update bill fields, items, prices, payment mode, etc.

**Request Body (all fields optional):**
```json
{
  "items_data": [
    {
      "item_name": "Updated Pizza",
      "price": "250.00",
      "mrp_price": "250.00",
      "quantity": "3",
      "subtotal": "750.00"
    }
  ],
  "payment_mode": "upi",
  "payment_reference": "UPI123456789",
  "amount_paid": "500.00",
  "customer_name": "Updated Customer",
  "subtotal": "750.00",
  "total_amount": "885.00"
}
```

**Note:** If `items_data` is provided, it replaces all existing items.

**Success Response (200):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "invoice_number": "INV-2026-01-27-0001",
  "items": [
    {
      "item_name": "Updated Pizza",
      "quantity": "3.00",
      "subtotal": "750.00"
    }
  ],
  "payment_mode": "upi",
  "payment_reference": "UPI123456789",
  "total_amount": "885.00",
  "updated_at": "2026-01-27T11:00:00Z"
}
```

**Example (cURL):**
```bash
curl -X PATCH http://localhost:8000/bills/880e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_mode": "upi",
    "payment_reference": "UPI123456789",
    "customer_name": "Updated Customer"
  }'
```

---

### Delete Bill

**DELETE** `/bills/<uuid:id>/`

**Requires authentication + vendor approval**

Delete a bill permanently.

**Success Response (204):**
```
No content
```

**Example (cURL):**
```bash
curl -X DELETE http://localhost:8000/bills/880e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## Bills (Direct CRUD Operations)

**Purpose:** Direct bill creation, update, and management operations. Use these endpoints when you want to create or modify bills directly on the server.

**Note:** For syncing existing bills between devices, use `/backup/sync` endpoints. To create new bills, use `/bills/` endpoints. See [Sales Backup (Multi-Device Sync Only)](#sales-backup-multi-device-sync-only) section.

### List Bills

**GET** `/bills/`

**Requires authentication + vendor approval**

List all bills for the vendor with filtering and pagination support.

**Query Parameters:**
- `billing_mode` (optional): Filter by billing mode (`gst` or `non_gst`)
- `start_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2026-01-01`)
- `end_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2026-01-31`)
- `payment_mode` (optional): Filter by payment mode (`cash`, `upi`, `card`, `credit`, `other`)
- `limit` (optional, default=100): Maximum number of bills to return
- `offset` (optional, default=0): Number of bills to skip (for pagination)

**Success Response (200):**
```json
{
  "count": 2,
  "total": 150,
  "offset": 0,
  "limit": 100,
  "bills": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "invoice_number": "INV-2026-01-27-0001",
      "bill_number": "BN-001",
      "bill_date": "2026-01-27",
      "billing_mode": "gst",
      "total_amount": "236.00",
      "item_count": 1,
      "payment_mode": "cash",
      "vendor_name": "ABC Restaurant",
      "created_at": "2026-01-27T10:00:00Z",
      "synced_at": "2026-01-27T10:00:00Z"
    }
  ]
}
```

**Example (cURL):**
```bash
# Get all bills
curl -X GET http://localhost:8000/bills/ \
  -H "Authorization: Token YOUR_TOKEN"

# Filter by billing mode
curl -X GET "http://localhost:8000/bills/?billing_mode=gst" \
  -H "Authorization: Token YOUR_TOKEN"

# Filter by date range
curl -X GET "http://localhost:8000/bills/?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Token YOUR_TOKEN"

# Pagination
curl -X GET "http://localhost:8000/bills/?limit=50&offset=100" \
  -H "Authorization: Token YOUR_TOKEN"
```

---

### Create Bill

**POST** `/bills/`

**Requires authentication + vendor approval**

Create a new bill directly on the server. **Invoice number is always auto-generated by the server** to ensure sequential numbering across all devices.

**Important:** 
- Server generates invoice number in format: `{prefix}-{date}-{number}` (e.g., "INV-2026-01-27-0001")
- Client cannot provide `invoice_number` - it will be ignored
- Server returns the generated invoice number in the response
- All devices receive sequential numbers from the server

**Request Body:**
```json
{
  "bill_date": "2026-01-27",
  "billing_mode": "gst",
  "items_data": [
    {
      "item_id": "item-uuid-1",
      "item_name": "Pizza Margherita",
      "price": "200.00",
      "mrp_price": "200.00",
      "price_type": "exclusive",
      "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
      "quantity": "2",
      "subtotal": "400.00",
      "item_gst_amount": "72.00",
      "veg_nonveg": "veg"
    }
  ],
  "subtotal": "400.00",
  "cgst_amount": "36.00",
  "sgst_amount": "36.00",
  "igst_amount": "0.00",
  "total_tax": "72.00",
  "total_amount": "472.00",
  "payment_mode": "cash",
  "amount_paid": "472.00",
  "customer_name": "John Doe",
  "customer_phone": "+91-9876543210"
}
```

**Field Descriptions:**
- `bill_date` (optional): Bill date (YYYY-MM-DD), defaults to today
- `billing_mode` (required): `"gst"` or `"non_gst"`
- `items_data` (required): Array of bill items
- `invoice_number` (ignored): Server always generates this - do not provide
- All other fields are optional

**Success Response (201):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "invoice_number": "INV-2026-01-27-0001",
  "bill_number": "INV-0001",
  "bill_date": "2026-01-27",
  "billing_mode": "gst",
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "item_name": "Pizza Margherita",
      "price": "200.00",
      "quantity": "2.00",
      "subtotal": "400.00",
      "item_gst_amount": "72.00"
    }
  ],
  "subtotal": "400.00",
  "total_amount": "472.00",
  "payment_mode": "cash",
  "created_at": "2026-01-27T10:00:00Z"
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/bills/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "billing_mode": "gst",
    "bill_date": "2026-01-27",
    "items_data": [
      {
        "item_name": "Pizza",
        "price": "200.00",
        "mrp_price": "200.00",
        "quantity": "2",
        "hsn_code": "2105",
        "hsn_gst_percentage": "18.00"
      }
    ],
    "subtotal": "400.00",
    "total_amount": "472.00",
    "payment_mode": "cash"
  }'
```

---

### Get Bill Details

**GET** `/bills/<uuid:id>/`

**Requires authentication + vendor approval**

Get detailed information about a specific bill including all items.

**Success Response (200):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "invoice_number": "INV-2026-01-27-0001",
  "bill_date": "2026-01-27",
  "billing_mode": "gst",
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "item_name": "Pizza Margherita",
      "price": "200.00",
      "mrp_price": "200.00",
      "quantity": "2.00",
      "subtotal": "400.00",
      "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
      "item_gst_amount": "72.00"
    }
  ],
  "subtotal": "400.00",
  "total_amount": "472.00",
  "payment_mode": "cash",
  "created_at": "2026-01-27T10:00:00Z"
}
```

**Example (cURL):**
```bash
curl -X GET http://localhost:8000/bills/880e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Token YOUR_TOKEN"
```

---

### Update Bill

**PATCH** `/bills/<uuid:id>/`

**Requires authentication + vendor approval**

Update an existing bill. Can update bill fields, items, prices, payment mode, etc.

**Request Body (all fields optional):**
```json
{
  "items_data": [
    {
      "item_name": "Updated Pizza",
      "price": "250.00",
      "mrp_price": "250.00",
      "quantity": "3",
      "subtotal": "750.00"
    }
  ],
  "payment_mode": "upi",
  "payment_reference": "UPI123456789",
  "amount_paid": "500.00",
  "customer_name": "Updated Customer",
  "subtotal": "750.00",
  "total_amount": "885.00"
}
```

**Note:** If `items_data` is provided, it replaces all existing items.

**Success Response (200):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "invoice_number": "INV-2026-01-27-0001",
  "items": [
    {
      "item_name": "Updated Pizza",
      "quantity": "3.00",
      "subtotal": "750.00"
    }
  ],
  "payment_mode": "upi",
  "payment_reference": "UPI123456789",
  "total_amount": "885.00",
  "updated_at": "2026-01-27T11:00:00Z"
}
```

**Example (cURL):**
```bash
curl -X PATCH http://localhost:8000/bills/880e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_mode": "upi",
    "payment_reference": "UPI123456789",
    "customer_name": "Updated Customer"
  }'
```

---

### Delete Bill

**DELETE** `/bills/<uuid:id>/`

**Requires authentication + vendor approval**

Delete a bill permanently.

**Success Response (204):**
```
No content
```

**Example (cURL):**
```bash
curl -X DELETE http://localhost:8000/bills/880e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## Sales Backup (Multi-Device Sync Only)

**Purpose:** These endpoints are specifically for syncing existing bills between devices. Use `/bills/` endpoints for creating new bills (server generates invoice numbers automatically). (Multi-Device Sync Only)

### Download Sales Data (GET)

**GET** `/backup/sync`

**Requires authentication + vendor approval**

Download bills from the server. This is used when a new device logs in with the same tenant to load existing sales history.

**Query Parameters:**
- `since` (optional): ISO timestamp - Only get bills synced after this time (e.g., `2026-01-01T10:00:00Z`)
- `limit` (optional, default=1000): Maximum number of bills to return
- `billing_mode` (optional): Filter by billing mode (`gst` or `non_gst`)
- `start_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2026-01-01`)
- `end_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2026-01-31`)

**Success Response (200):**
```json
{
  "count": 2,
  "vendor_id": "vendor-uuid",
  "vendor_name": "ABC Restaurant",
  "bills": [
    {
      "id": "bill-uuid-1",
      "invoice_number": "INV-2026-01-27-0001",
      "bill_number": "BN-2026-001",
      "bill_date": "2026-01-01",
      "billing_mode": "gst",
      "restaurant_name": "ABC Restaurant",
      "address": "123 Main St",
      "gstin": "29ABCDE1234F1Z5",
      "fssai_license": "12345678901234",
      "logo_url": "https://bucket.s3.region.amazonaws.com/vendors/.../logo.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
      "footer_note": "Thank you!",
      "subtotal": "200.00",
      "total_amount": "236.00",
      "total_tax": "36.00",
      "cgst_amount": "18.00",
      "sgst_amount": "18.00",
      "igst_amount": "0.00",
      "payment_mode": "cash",
      "items": [
        {
          "id": "billitem-uuid-1",
          "item": "item-uuid-1",
          "item_id": "item-uuid-1",
          "item_name": "Product A",
          "price": "100.00",
          "mrp_price": "100.00",
          "price_type": "exclusive",
          "quantity": "2.00",
          "subtotal": "200.00",
          "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
          "item_gst_amount": "36.00",
          "veg_nonveg": "veg"
        }
      ],
      "item_count": 1,
      "total_quantity": 2.0,
      "created_at": "2026-01-01T10:00:00Z",
      "synced_at": "2026-01-01T10:00:00Z"
    }
  ]
}
```

**Example Requests:**
```bash
# Get all bills
curl -X GET http://localhost:8000/backup/sync \
  -H "Authorization: Token <token>"

# Get GST bills only
curl -X GET "http://localhost:8000/backup/sync?billing_mode=gst" \
  -H "Authorization: Token <token>"

# Get bills since a specific date
curl -X GET "http://localhost:8000/backup/sync?since=2026-01-01T00:00:00Z&limit=100" \
  -H "Authorization: Token <token>"

# Get bills for a date range
curl -X GET "http://localhost:8000/backup/sync?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Token <token>"
```

---

### Upload Sales Data (POST)

**POST** `/backup/sync`

**Requires authentication + vendor approval**

Batch upload sales/bill data for syncing existing bills between devices. Accepts single bill or array of bills.

**Important:**
- **`invoice_number` is REQUIRED** - This endpoint is only for syncing existing bills, not creating new ones
- To create new bills, use `POST /bills/` which automatically generates invoice numbers
- Server checks if bill already exists by `invoice_number` - if exists, skips (prevents duplicates)
- If bill doesn't exist, creates it with the provided `invoice_number`

**Use Cases:**
- Syncing bills from one device to another
- Restoring bills from backup
- Syncing bills created before system migration

**Request Body (Single Bill):**

**GST Bill Example (Complete Format):**
```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0001",
    "bill_id": "bill-123",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "logo_url": "https://bucket.s3.region.amazonaws.com/vendors/vendor-id/logo.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
    "bill_number": "BN-2026-001",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "item_id": "master-item-uuid-1",
        "name": "Product A",
        "description": "Product description",
        "price": 100.00,
        "mrp_price": 100.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 2,
        "subtotal": 200.00,
        "item_gst": 36.00,
        "veg_nonveg": "veg",
        "unit": "pcs"
      }
    ],
    "subtotal": 200.00,
    "cgst": 18.00,
    "sgst": 18.00,
    "igst": 0.00,
    "total_tax": 36.00,
    "total": 236.00,
    "footer_note": "Thank you for visiting!",
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Non-GST Bill Example (Complete Format):**
```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0002",
    "bill_id": "bill-124",
    "billing_mode": "non_gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "logo_url": "https://bucket.s3.region.amazonaws.com/vendors/vendor-id/logo.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
    "bill_number": "BN-2026-002",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "item_id": "master-item-uuid-1",
        "name": "Product B",
        "description": "Product description",
        "price": 150.00,
        "mrp_price": 150.00,
        "price_type": "exclusive",
        "quantity": 1,
        "subtotal": 150.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 150.00,
    "total": 150.00,
    "footer_note": "Thank you for visiting!",
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

---

## Complete Bill Creation Examples - All Cases

### Example 1: GST Bill - Intra-State - Cash Payment - No Discounts

**Scenario:** Customer pays with cash, all items are intra-state (CGST + SGST), no discounts applied.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0003",
    "bill_id": "bill-125",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_number": "BN-2026-003",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "item_id": "master-item-uuid-1",
        "name": "Pizza Margherita",
        "price": 200.00,
        "mrp_price": 200.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 2,
        "subtotal": 400.00,
        "item_gst": 72.00,
        "veg_nonveg": "veg"
      },
      {
        "id": "item-uuid-2",
        "item_id": "master-item-uuid-2",
        "name": "Coca Cola",
        "price": 50.00,
        "mrp_price": 50.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 50.00,
        "item_gst": 9.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 450.00,
    "cgst": 40.50,
    "sgst": 40.50,
    "igst": 0.00,
    "total_tax": 81.00,
    "total": 531.00,
    "payment_mode": "cash",
    "amount_paid": 531.00,
    "change_amount": 0.00,
    "discount_percentage": 0.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/backup/sync \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bill_data": {
      "invoice_number": "INV-2026-01-27-0003",
      "billing_mode": "gst",
      "restaurant_name": "ABC Restaurant",
      "address": "123 Main St",
      "gstin": "29ABCDE1234F1Z5",
      "fssai_license": "12345678901234",
      "bill_date": "2026-01-01",
      "items": [
        {
          "id": "item-uuid-1",
          "name": "Pizza Margherita",
          "price": 200.00,
          "mrp_price": 200.00,
          "price_type": "exclusive",
          "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
          "quantity": 2,
          "subtotal": 400.00,
          "item_gst": 72.00,
          "veg_nonveg": "veg"
        }
      ],
      "subtotal": 400.00,
      "cgst": 36.00,
      "sgst": 36.00,
      "igst": 0.00,
      "total_tax": 72.00,
      "total": 472.00,
      "payment_mode": "cash",
      "amount_paid": 472.00
    },
    "device_id": "device-001"
  }'
```

---

### Example 2: GST Bill - Intra-State - UPI Payment - No Discounts

**Scenario:** Customer pays with UPI, intra-state transaction.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0004",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Burger",
        "price": 150.00,
        "mrp_price": 150.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 150.00,
        "item_gst": 27.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 150.00,
    "cgst": 13.50,
    "sgst": 13.50,
    "igst": 0.00,
    "total_tax": 27.00,
    "total": 177.00,
    "payment_mode": "upi",
    "payment_reference": "UPI123456789",
    "amount_paid": 177.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

---

### Example 3: GST Bill - Intra-State - Card Payment - No Discounts

**Scenario:** Customer pays with card, intra-state transaction.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0005",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Pasta",
        "price": 180.00,
        "mrp_price": 180.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 180.00,
        "item_gst": 32.40,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 180.00,
    "cgst": 16.20,
    "sgst": 16.20,
    "igst": 0.00,
    "total_tax": 32.40,
    "total": 212.40,
    "payment_mode": "card",
    "payment_reference": "CARD987654321",
    "amount_paid": 212.40,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

---

### Example 4: GST Bill - Intra-State - Credit Payment - No Discounts

**Scenario:** Customer pays on credit (pending payment), intra-state transaction.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0006",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Dinner Combo",
        "price": 500.00,
        "mrp_price": 500.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 500.00,
        "item_gst": 90.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 500.00,
    "cgst": 45.00,
    "sgst": 45.00,
    "igst": 0.00,
    "total_tax": 90.00,
    "total": 590.00,
    "payment_mode": "credit",
    "amount_paid": 0.00,
    "customer_name": "John Doe",
    "customer_phone": "+91-9876543210",
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Note:** For credit payments, `amount_paid` is typically 0 or less than `total`, indicating pending payment.

---

### Example 5: GST Bill - Intra-State - Other Payment - No Discounts

**Scenario:** Customer pays with other payment method (e.g., wallet, cheque), intra-state transaction.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0007",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Snacks",
        "price": 100.00,
        "mrp_price": 100.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 100.00,
        "item_gst": 18.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 100.00,
    "cgst": 9.00,
    "sgst": 9.00,
    "igst": 0.00,
    "total_tax": 18.00,
    "total": 118.00,
    "payment_mode": "other",
    "payment_reference": "WALLET123456",
    "amount_paid": 118.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

---

### Example 6: GST Bill - Inter-State - Cash Payment - No Discounts

**Scenario:** Customer from different state, inter-state transaction (IGST only).

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0008",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Pizza",
        "price": 300.00,
        "mrp_price": 300.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 300.00,
        "item_gst": 54.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 300.00,
    "cgst": 0.00,
    "sgst": 0.00,
    "igst": 54.00,
    "total_tax": 54.00,
    "total": 354.00,
    "payment_mode": "cash",
    "amount_paid": 354.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Note:** For inter-state transactions, use IGST only (CGST and SGST are 0).

---

### Example 7: GST Bill - Inter-State - UPI Payment - No Discounts

**Scenario:** Inter-state transaction, UPI payment.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0009",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Biryani",
        "price": 250.00,
        "mrp_price": 250.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 250.00,
        "item_gst": 45.00,
        "veg_nonveg": "nonveg"
      }
    ],
    "subtotal": 250.00,
    "cgst": 0.00,
    "sgst": 0.00,
    "igst": 45.00,
    "total_tax": 45.00,
    "total": 295.00,
    "payment_mode": "upi",
    "payment_reference": "UPI987654321",
    "amount_paid": 295.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

---

### Example 8: GST Bill - Intra-State - Cash Payment - With Percentage Discount

**Scenario:** Customer pays with cash, 10% discount applied to subtotal (before tax).

**Calculation:**
- Subtotal: 400.00 (2 × Pizza @ 200.00)
- Tax: 72.00 (18% GST on 400.00)
- Total before discount: 472.00
- Discount (10%): 47.20 (10% of 472.00)
- Final total: 424.80

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0010",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Pizza",
        "price": 200.00,
        "mrp_price": 200.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 2,
        "subtotal": 400.00,
        "item_gst": 72.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 400.00,
    "cgst": 36.00,
    "sgst": 36.00,
    "igst": 0.00,
    "total_tax": 72.00,
    "discount_percentage": 10.00,
    "discount_amount": 40.00, // 10% of subtotal (400.00)
    "total": 432.00, // (400.00 - 40.00) + 72.00
    "payment_mode": "cash",
    "amount_paid": 432.00,
    "change_amount": 0.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Note:** 
- `discount_percentage` is the discount percentage (e.g., 10.00 for 10%)
- Discount is applied to **subtotal** (before tax)
- `discount_amount` is automatically calculated by server (read-only in API responses)
- Item-level discounts have been removed - all discounts are bill-level percentage only

---

### Example 9: Non-GST Bill - Cash Payment - No Discounts

**Scenario:** Non-GST bill, cash payment, no discounts.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0011",
    "billing_mode": "non_gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Tea",
        "price": 20.00,
        "mrp_price": 20.00,
        "price_type": "exclusive",
        "quantity": 2,
        "subtotal": 40.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 40.00,
    "total": 40.00,
    "payment_mode": "cash",
    "amount_paid": 40.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Note:** For Non-GST bills, no tax fields are required. `total` should equal `subtotal`.

---

### Example 10: Non-GST Bill - UPI Payment - No Discounts

**Scenario:** Non-GST bill, UPI payment.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0012",
    "billing_mode": "non_gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Coffee",
        "price": 30.00,
        "mrp_price": 30.00,
        "price_type": "exclusive",
        "quantity": 1,
        "subtotal": 30.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 30.00,
    "total": 30.00,
    "payment_mode": "upi",
    "payment_reference": "UPI111222333",
    "amount_paid": 30.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

---

### Example 11: GST Bill - With Linked Items (item_id present)

**Scenario:** Bill items are linked to master Item records for analytics.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0013",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "billitem-uuid-1",
        "item_id": "master-item-uuid-1",
        "name": "Pizza Margherita",
        "price": 200.00,
        "mrp_price": 200.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 200.00,
        "item_gst": 36.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 200.00,
    "cgst": 18.00,
    "sgst": 18.00,
    "igst": 0.00,
    "total_tax": 36.00,
    "total": 236.00,
    "payment_mode": "cash",
    "amount_paid": 236.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Note:** When `item_id` is provided and matches an existing Item, the bill item is linked to the master Item for analytics.

---

### Example 12: GST Bill - With Additional Items (no item_id)

**Scenario:** Bill contains additional items not in the master Item list.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0014",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "billitem-uuid-1",
        "name": "Special Dish (Not in Menu)",
        "price": 350.00,
        "mrp_price": 350.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 350.00,
        "item_gst": 63.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 350.00,
    "cgst": 31.50,
    "sgst": 31.50,
    "igst": 0.00,
    "total_tax": 63.00,
    "total": 413.00,
    "payment_mode": "cash",
    "amount_paid": 413.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Note:** When `item_id` is not provided, the item is stored as an additional item (not linked to master Item).

---

### Example 13: GST Bill - Mixed Items (Some Linked, Some Additional)

**Scenario:** Bill contains both linked items and additional items.

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0015",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "billitem-uuid-1",
        "item_id": "master-item-uuid-1",
        "name": "Pizza Margherita",
        "price": 200.00,
        "mrp_price": 200.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 200.00,
        "item_gst": 36.00,
        "veg_nonveg": "veg"
      },
      {
        "id": "billitem-uuid-2",
        "name": "Special Combo (Not in Menu)",
        "price": 300.00,
        "mrp_price": 300.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 300.00,
        "item_gst": 54.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 500.00,
    "cgst": 45.00,
    "sgst": 45.00,
    "igst": 0.00,
    "total_tax": 90.00,
    "total": 590.00,
    "payment_mode": "cash",
    "amount_paid": 590.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

---

### Example 14: GST Bill - Multiple Items with Different GST Percentages

**Scenario:** Bill contains items with different GST rates (0%, 5%, 8%, 18%).

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0016",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "billitem-uuid-1",
        "name": "Rice (0% GST)",
        "price": 50.00,
        "mrp_price": 50.00,
        "price_type": "exclusive",
        "hsn_code": "2106",
        "hsn_gst_percentage": 0.00,
        "quantity": 1,
        "subtotal": 50.00,
        "item_gst": 0.00,
        "veg_nonveg": "veg"
      },
      {
        "id": "billitem-uuid-2",
        "name": "Tea (5% GST)",
        "price": 20.00,
        "mrp_price": 20.00,
        "price_type": "exclusive",
        "hsn_code": "2106",
        "hsn_gst_percentage": 5.00,
        "quantity": 2,
        "subtotal": 40.00,
        "item_gst": 2.00,
        "veg_nonveg": "veg"
      },
      {
        "id": "billitem-uuid-3",
        "name": "Snacks (8% GST)",
        "price": 100.00,
        "mrp_price": 100.00,
        "price_type": "exclusive",
        "hsn_code": "2106",
        "hsn_gst_percentage": 12.00,
        "quantity": 1,
        "subtotal": 100.00,
        "item_gst": 8.00,
        "veg_nonveg": "veg"
      },
      {
        "id": "billitem-uuid-4",
        "name": "Pizza (18% GST)",
        "price": 200.00,
        "mrp_price": 200.00,
        "price_type": "exclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 200.00,
        "item_gst": 36.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 390.00,
    "cgst": 23.00,
    "sgst": 23.00,
    "igst": 0.00,
    "total_tax": 46.00,
    "total": 436.00,
    "payment_mode": "cash",
    "amount_paid": 436.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Note:** Total tax = Sum of all item_gst amounts. CGST and SGST are split equally (50-50) for intra-state.

---

### Example 15: GST Bill - Inclusive Pricing

**Scenario:** Items use inclusive pricing (GST already included in MRP).

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0017",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "billitem-uuid-1",
        "name": "Pizza (Inclusive)",
        "price": 200.00,
        "mrp_price": 236.00,
        "price_type": "inclusive",
        "hsn_code": "2105",
        "hsn_gst_percentage": 18.00,
        "quantity": 1,
        "subtotal": 236.00,
        "item_gst": 36.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 236.00,
    "cgst": 18.00,
    "sgst": 18.00,
    "igst": 0.00,
    "total_tax": 36.00,
    "total": 236.00,
    "payment_mode": "cash",
    "amount_paid": 236.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Note:** For inclusive pricing, MRP already includes GST. The GST amount is extracted from MRP for calculation.

---

### Example 16: Non-GST Bill - With Percentage Discount

**Scenario:** Non-GST bill with 15% discount applied to subtotal.

**Calculation:**
- Subtotal: 100.00 (5 × Tea @ 20.00)
- Total before discount: 100.00 (no tax for non-GST)
- Discount (15%): 15.00 (15% of 100.00)
- Final total: 85.00

```json
{
  "bill_data": {
    "invoice_number": "INV-2026-01-27-0018",
    "billing_mode": "non_gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "bill_date": "2026-01-01",
    "items": [
      {
        "id": "billitem-uuid-1",
        "name": "Tea",
        "price": 20.00,
        "mrp_price": 20.00,
        "price_type": "exclusive",
        "quantity": 5,
        "subtotal": 100.00,
        "veg_nonveg": "veg"
      }
    ],
    "subtotal": 100.00,
    "discount_percentage": 15.00,
    "discount_amount": 15.00, // 15% of subtotal (100.00)
    "total": 85.00, // 100.00 - 15.00
    "payment_mode": "cash",
    "amount_paid": 85.00,
    "timestamp": "2026-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Note:** 
- `discount_percentage` is the discount percentage (e.g., 15.00 for 15%)
- Discount is applied to **subtotal** (before tax)
- `discount_amount` is automatically calculated by server (read-only in API responses)

---

### Payment Mode Summary

**Available Payment Modes:**
- `"cash"` - Cash payment
- `"upi"` - UPI payment (include `payment_reference` for transaction ID)
- `"card"` - Card payment (include `payment_reference` for card transaction ID)
- `"credit"` - Credit payment (pending payment, `amount_paid` typically 0 or less than `total`)
- `"other"` - Other payment methods (wallet, cheque, etc. - include `payment_reference`)

**For Credit Payments:**
- Set `payment_mode: "credit"`
- Set `amount_paid: 0.00` or amount less than `total`
- Include `customer_name` and `customer_phone` for tracking
- Outstanding amount = `total - amount_paid`

**Bill Data Structure (Complete):**

**Required Fields (All Bills):**
- `invoice_number`: Invoice number (format: `{prefix}-{date}-{number}`, e.g., "INV-2026-01-27-0001")
  - **For `POST /bills/`:** Server automatically generates this - do NOT provide it
  - **For `POST /backup/sync`:** REQUIRED - must provide existing invoice_number (for syncing existing bills only)
- `bill_id`: Unique bill identifier (UUID)
- `billing_mode`: `"gst"` or `"non_gst"` - Determines if GST calculations are applied
- `restaurant_name`: Restaurant/Vendor business name
- `address`: Restaurant/Vendor address
- `gstin`: GST Number (GSTIN)
- `fssai_license`: FSSAI License Number (required for restaurant bills)
- `bill_number`: Bill number (can be same as invoice_number or separate)
- `bill_date`: Bill date (YYYY-MM-DD format, mandatory with bill number)
- `items`: Array of bill items with item details
- `subtotal`: Total before tax
- `total`: Final total amount
- `timestamp`: ISO 8601 timestamp

**Optional Fields:**
- `logo_url`: URL to restaurant logo (from vendor.logo)
- `footer_note`: Footer note to display on bill (from vendor.footer_note)

**For GST Bills (`billing_mode: "gst"`):**

**Tax Calculation (HSN/SAC Based):**
- **If vendor has SAC code set:**
  - All items use the vendor's `sac_gst_percentage` for tax calculation
  - Each item's tax = `item_subtotal × sac_gst_percentage / 100`
  - Total tax = sum of all item taxes
  - CGST = total_tax / 2, SGST = total_tax / 2 (intra-state)
  - IGST = total_tax (inter-state)
- **If vendor does NOT have SAC code:**
  - Each item uses its own `hsn_code` and `hsn_gst_percentage` for tax calculation
  - Each item's tax = `item_subtotal × hsn_gst_percentage / 100`
  - Total tax = sum of all item taxes
  - Different items can have different HSN codes and different GST rates
  - CGST = total_tax / 2, SGST = total_tax / 2 (intra-state)
  - IGST = total_tax (inter-state)
- **Tax fields in bill:**
  - `cgst`: Central GST amount (for intra-state)
  - `sgst`: State GST amount (for intra-state)
  - `igst`: Integrated GST amount (for inter-state, 0 for intra-state)
  - `total_tax`: Sum of all taxes (cgst + sgst + igst)

**Note:** SAC codes are ideal for service-based businesses (restaurants, hotels, catering). HSN codes are used for goods/products where each item can have different tax rates.

**For Non-GST Bills (`billing_mode: "non_gst"`):**
- No tax fields required
- `total` should equal `subtotal`
- Product GST should NOT be added to totaling bill

**Item Structure in Bills (items array):**

**Required Fields:**
- `id`: Item UUID (unique identifier for this bill item)
- `name`: Item name (required)
- `price`: Base price (required)
- `mrp_price`: MRP price (required - exclusive or inclusive based on price_type)
- `quantity`: Quantity purchased (required)
- `subtotal`: Item subtotal (required - mrp_price * quantity)

**Optional Fields:**
- `item_id`: Master Item UUID (optional - links to master Item record if provided and exists)
- `price_type`: `"exclusive"` or `"inclusive"` (default: "exclusive")
  - **Exclusive**: GST not included in MRP (GST added separately)
  - **Inclusive**: GST included in MRP (GST already in price)
- `hsn_code`: HSN code for this item (optional, e.g., "2106", "2202")
- `hsn_gst_percentage`: GST percentage for this HSN code (optional, e.g., 5.00 for 5%)
- `gst_percentage`: GST percentage at time of sale (calculated from HSN/SAC, read-only in response)
- `item_gst`: GST amount for this item (only for GST bills, calculated automatically)
- `veg_nonveg`: `"veg"` or `"nonveg"` (optional)
- `description`: Item description (optional)
- `unit`: Unit of measurement (optional, e.g., "kg", "L", "pcs")
- `batch_number`: Batch number (optional)
- `expiry_date`: Expiry date in YYYY-MM-DD format (optional)

**Note:** If `item_id` is provided and matches an existing Item in the system, the bill item will be linked to the master Item record for historical accuracy and analytics.

**Bill Format Requirements:**

**GST Bill Format (Compulsory Fields on Bill):**
1. Invoice number
2. Restaurant Name
3. Address
4. GSTIN
5. FSSAI License No
6. Bill Number & Date
7. Item-wise amount
8. GST breakup (CGST + SGST)
9. Total Amount

**Non-GST Bill Format (Compulsory Fields on Bill):**
1. Invoice number
2. Restaurant Name
3. Address
4. GSTIN
5. FSSAI License No
6. Bill Number & Date
7. Item-wise amount
8. Total Amount (no GST breakup)

**Invoice Numbering:**
- Auto-generated and sequential
- Calculated according to billing times
- Date is mandatorily attached with billing number
- Syncs with both GST and non-GST bills according to sequence
- Invoice reset option not needed

**Request Body (Multiple Bills):**
```json
[
  {
    "bill_data": {...},
    "device_id": "device-001"
  },
  {
    "bill_data": {...},
    "device_id": "device-001"
  }
]
```

**Success Response (201):**
```json
{
  "synced": 2,
  "bills": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "vendor": "550e8400-e29b-41d4-a716-446655440010",
      "vendor_name": "ABC Restaurant",
      "device_id": "device-001",
      "invoice_number": "INV-2026-01-27-0001",
      "bill_number": "BN-2026-001",
      "bill_date": "2026-01-01",
      "billing_mode": "gst",
      "restaurant_name": "ABC Restaurant",
      "address": "123 Main St",
      "gstin": "29ABCDE1234F1Z5",
      "fssai_license": "12345678901234",
      "logo_url": "https://bucket.s3.region.amazonaws.com/vendors/.../logo.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&...",
      "footer_note": "Thank you!",
      "subtotal": "200.00",
      "total_amount": "236.00",
      "total_tax": "36.00",
      "cgst_amount": "18.00",
      "sgst_amount": "18.00",
      "igst_amount": "0.00",
      "payment_mode": "cash",
      "items": [
        {
          "id": "billitem-uuid-1",
          "item": "item-uuid-1",
          "item_id": "item-uuid-1",
          "item_name": "Product A",
          "price": "100.00",
          "mrp_price": "100.00",
          "price_type": "exclusive",
          "quantity": "2.00",
          "subtotal": "200.00",
          "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
          "item_gst_amount": "36.00",
          "veg_nonveg": "veg"
        }
      ],
      "item_count": 1,
      "total_quantity": 2.0,
      "created_at": "2026-01-01T10:00:00Z",
      "synced_at": "2026-01-01T10:00:00Z",
      "updated_at": "2026-01-01T10:00:00Z"
    },
    ...
  ],
  "errors": []  // Only present if some bills failed to sync
}
```

**Discount System:**
- **Percentage-Based Only**: Discounts are applied using `discount_percentage` (e.g., 10.00 for 10% discount)
- **Applied to Subtotal**: Discount percentage is applied to the subtotal (before tax)
- **Calculation**: `discount_amount = subtotal × discount_percentage / 100`
- **Final Total**: `final_total = (subtotal - discount_amount) + total_tax`
- **Final Total**: `total_amount = (subtotal + tax) - discount_amount`
- **Item-Level Discounts Removed**: All discounts are bill-level percentage only (no item-level discounts)
- **Auto-Calculated**: `discount_amount` is automatically calculated by the server from `discount_percentage` (read-only in API responses)

**Important Notes:**
- Bills are stored in a **structured, relational format** (Bill and BillItem models) instead of JSON blobs
- This makes the system **fully extendable** for future business logic:
  - Analytics and reporting (e.g., "Show top 5 selling items")
  - Inventory deduction (automatically reduce stock when bill is created)
  - Tax reporting (e.g., "Calculate total CGST payable for March")
  - Customer loyalty programs
  - Advanced filtering and querying
- **Duplicate Handling**: If a bill with the same `invoice_number` already exists for the vendor, the server will skip it (no error)
- **Passive Receiver**: Server accepts bills even with missing optional fields or invalid data structure
- **Item Linking**: If `item_id` is provided in bill items and matches an existing Item, the bill item will be linked to the master Item record

---

## Dashboard & Analytics

The dashboard endpoints provide analytics and insights for vendors. All endpoints require authentication and return data filtered by the authenticated vendor.

**Base URL:** `/dashboard/`

**Authentication:** All endpoints require Token Authentication.

---

### Dashboard Stats

**GET** `/dashboard/stats`

**Requires authentication**

Get overall dashboard statistics including total bills, revenue, tax collected, and payment split.

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD format (default: today)
- `end_date` (optional): YYYY-MM-DD format (default: today)

**Success Response (200):**
```json
{
  "vendor_id": "550e8400-e29b-41d4-a716-446655440000",
  "vendor_name": "ABC Restaurant",
  "date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  },
  "statistics": {
    "total_bills": 150,
    "gst_bills": 100,
    "non_gst_bills": 50,
    "total_revenue": "50000.00",
    "total_tax_collected": "9000.00",
    "payment_split": {
      "cash": {
        "count": 80,
        "amount": "30000.00"
      },
      "upi": {
        "count": 50,
        "amount": "15000.00"
      },
      "card": {
        "count": 20,
        "amount": "5000.00"
      },
      "credit": {
        "count": 0,
        "amount": "0.00"
      },
      "other": {
        "count": 0,
        "amount": "0.00"
      }
    }
  }
}
```

**Example (cURL):**
```bash
curl -X GET "http://localhost:8000/dashboard/stats/?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

### Sales Analytics

**GET** `/dashboard/sales`

**Requires authentication**

Get detailed sales analytics filtered by billing mode (GST/Non-GST) with daily breakdown.

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD format (default: today)
- `end_date` (optional): YYYY-MM-DD format (default: today)
- `billing_mode` (optional): `gst` or `non_gst` (default: all)

**Success Response (200):**
```json
{
  "vendor_id": "550e8400-e29b-41d4-a716-446655440000",
  "date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  },
  "filters": {
    "billing_mode": "gst"
  },
  "summary": {
    "total_bills": 100,
    "total_revenue": "35000.00",
    "total_subtotal": "29661.02",
    "total_tax": "5338.98",
    "total_cgst": "2669.49",
    "total_sgst": "2669.49",
    "total_discount": "500.00"
  },
  "daily_breakdown": [
    {
      "date": "2026-01-01",
      "bills_count": 10,
      "revenue": "3500.00",
      "tax": "533.90"
    },
    {
      "date": "2026-01-02",
      "bills_count": 8,
      "revenue": "2800.00",
      "tax": "427.12"
    }
  ]
}
```

**Example (cURL):**
```bash
curl -X GET "http://localhost:8000/dashboard/sales/?billing_mode=gst&start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

### Item Analytics

**GET** `/dashboard/items`

**Requires authentication**

Get most/least sold dishes with sales statistics.

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD format (default: today)
- `end_date` (optional): YYYY-MM-DD format (default: today)
- `sort` (optional): `most_sold` or `least_sold` (default: `most_sold`)
- `limit` (optional): Integer, number of items to return (default: 10)

**Success Response (200):**
```json
{
  "vendor_id": "550e8400-e29b-41d4-a716-446655440000",
  "date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  },
  "sort": "most_sold",
  "items": [
    {
      "item_name": "Coca Cola",
      "item_id": "item-uuid-1",
      "category": ["Beverages"],
      "veg_nonveg": "veg",
      "total_quantity": "150.00",
      "total_revenue": "3750.00",
      "bill_count": 120
    },
    {
      "item_name": "Pizza Margherita",
      "item_id": "item-uuid-2",
      "category": ["Dinner"],
      "veg_nonveg": "veg",
      "total_quantity": "80.00",
      "total_revenue": "8000.00",
      "bill_count": 75
    }
  ]
}
```

**Example (cURL):**
```bash
# Most sold items
curl -X GET "http://localhost:8000/dashboard/items/?sort=most_sold&limit=10" \
  -H "Authorization: Token YOUR_TOKEN_HERE"

# Least sold items
curl -X GET "http://localhost:8000/dashboard/items/?sort=least_sold&limit=10" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

### Payment Analytics

**GET** `/dashboard/payments`

**Requires authentication**

Get transaction split by payment mode (Cash/Card/UPI/Credit/Other).

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD format (default: today)
- `end_date` (optional): YYYY-MM-DD format (default: today)

**Success Response (200):**
```json
{
  "vendor_id": "550e8400-e29b-41d4-a716-446655440000",
  "date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  },
  "summary": {
    "total_transactions": 150,
    "total_revenue": "50000.00"
  },
  "payment_split": [
    {
      "payment_mode": "cash",
      "transaction_count": 80,
      "total_amount": "30000.00",
      "percentage": "60.00"
    },
    {
      "payment_mode": "upi",
      "transaction_count": 50,
      "total_amount": "15000.00",
      "percentage": "30.00"
    },
    {
      "payment_mode": "card",
      "transaction_count": 20,
      "total_amount": "5000.00",
      "percentage": "10.00"
    }
  ]
}
```

**Example (cURL):**
```bash
curl -X GET "http://localhost:8000/dashboard/payments/?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

### Tax Analytics

**GET** `/dashboard/tax`

**Requires authentication**

Get total tax (GST) collected with breakdown by GST percentage.

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD format (default: today)
- `end_date` (optional): YYYY-MM-DD format (default: today)

**Success Response (200):**
```json
{
  "vendor_id": "550e8400-e29b-41d4-a716-446655440000",
  "date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  },
  "summary": {
    "gst_bills_count": 100,
    "total_tax_collected": "9000.00",
    "cgst_collected": "4500.00",
    "sgst_collected": "4500.00",
    "igst_collected": "0.00"
  },
  "tax_by_percentage": [
    {
      "hsn_code": "2105",
  "hsn_gst_percentage": "18.00",
      "item_count": 500,
      "tax_collected": "5400.00"
    },
    {
      "hsn_code": "2106",
    "hsn_gst_percentage": "5.00",
      "item_count": 200,
      "tax_collected": "2500.00"
    },
    {
      "hsn_code": "2106",
    "hsn_gst_percentage": "0.00",
      "item_count": 100,
      "tax_collected": "0.00"
    }
  ]
}
```

**Example (cURL):**
```bash
curl -X GET "http://localhost:8000/dashboard/tax/?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

### Profit Analytics

**GET** `/dashboard/profit`

**Requires authentication**

Get net profit calculation (estimated based on revenue and cost assumptions).

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD format (default: today)
- `end_date` (optional): YYYY-MM-DD format (default: today)

**Note:** Profit calculation is estimated based on a 60% cost assumption. For accurate profit, actual cost data is required (cost_price field in Item model).

**Success Response (200):**
```json
{
  "vendor_id": "550e8400-e29b-41d4-a716-446655440000",
  "date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  },
  "profit_calculation": {
    "total_revenue": "50000.00",
    "estimated_cost": "30000.00",
    "estimated_cost_percentage": "60.00",
    "gross_profit": "20000.00",
    "net_profit": "20000.00",
    "profit_margin_percentage": "40.00"
  },
  "note": "Profit calculation is estimated based on 60% cost assumption. For accurate profit, actual cost data is required."
}
```

**Example (cURL):**
```bash
curl -X GET "http://localhost:8000/dashboard/profit/?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

### Pending Payments & Dues

**GET** `/dashboard/dues`

**Requires authentication**

Get pending payments and outstanding dues (credit bills and partial payments).

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD format (default: today)
- `end_date` (optional): YYYY-MM-DD format (default: today)

**Success Response (200):**
```json
{
  "vendor_id": "550e8400-e29b-41d4-a716-446655440000",
  "date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  },
  "summary": {
    "total_pending_bills": 5,
    "total_outstanding_amount": "2500.00",
    "credit_bills_count": 3,
    "partial_payment_bills_count": 2
  },
  "pending_bills": [
    {
      "bill_id": "770e8400-e29b-41d4-a716-446655440000",
      "invoice_number": "INV-2026-01-27-0006",
      "bill_date": "2026-01-15",
      "customer_name": "John Doe",
      "customer_phone": "+91-9876543210",
      "total_amount": "590.00",
      "amount_paid": "0.00",
      "outstanding_amount": "590.00",
      "payment_mode": "credit",
      "days_pending": 8
    },
    {
      "bill_id": "770e8400-e29b-41d4-a716-446655440001",
      "invoice_number": "INV-2026-01-27-0010",
      "bill_date": "2026-01-20",
      "customer_name": "Jane Smith",
      "customer_phone": "+91-9876543211",
      "total_amount": "1000.00",
      "amount_paid": "500.00",
      "outstanding_amount": "500.00",
      "payment_mode": "cash",
      "days_pending": 3
    },
    {
      "bill_id": "770e8400-e29b-41d4-a716-446655440002",
      "invoice_number": "INV-2026-01-27-0012",
      "bill_date": "2026-01-18",
      "customer_name": "Bob Johnson",
      "customer_phone": "+91-9876543212",
      "total_amount": "1200.00",
      "amount_paid": "0.00",
      "outstanding_amount": "1200.00",
      "payment_mode": "credit",
      "days_pending": 5
    }
  ]
}
```

**Example 1: Get Pending Payments for Today (cURL):**
```bash
curl -X GET "http://localhost:8000/dashboard/dues" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

**Example 2: Get Pending Payments for Date Range (cURL):**
```bash
curl -X GET "http://localhost:8000/dashboard/dues?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

**Example 3: JavaScript/Fetch:**
```javascript
// Get pending payments for today
async function getPendingPayments(token) {
  const response = await fetch('http://localhost:8000/dashboard/dues', {
    method: 'GET',
    headers: {
      'Authorization': `Token ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (response.ok) {
    const data = await response.json();
    console.log(`Total Pending Bills: ${data.summary.total_pending_bills}`);
    console.log(`Total Outstanding: ₹${data.summary.total_outstanding_amount}`);
    
    // Display pending bills
    data.pending_bills.forEach(bill => {
      console.log(`${bill.invoice_number}: ₹${bill.outstanding_amount} (${bill.days_pending} days pending)`);
    });
    
    return data;
  } else {
    const error = await response.json();
    console.error('Error:', error);
    throw new Error(error.error || 'Failed to fetch pending payments');
  }
}

// Get pending payments for date range
async function getPendingPaymentsByDateRange(token, startDate, endDate) {
  const url = `http://localhost:8000/dashboard/dues?start_date=${startDate}&end_date=${endDate}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Token ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (response.ok) {
    return await response.json();
  } else {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch pending payments');
  }
}

// Usage
const token = 'your-token-here';
getPendingPayments(token)
  .then(data => {
    console.log('Pending payments loaded:', data);
  })
  .catch(error => {
    console.error('Error loading pending payments:', error);
  });
```

**Example 4: React Native:**
```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

function PendingPaymentsScreen() {
  const [pendingBills, setPendingBills] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPendingPayments();
  }, []);

  const loadPendingPayments = async (startDate = null, endDate = null) => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('auth_token');
      
      let url = 'http://your-server.com/dashboard/dues';
      if (startDate && endDate) {
        url += `?start_date=${startDate}&end_date=${endDate}`;
      }
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPendingBills(data.pending_bills);
        setSummary(data.summary);
        setError(null);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load pending payments');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderBillItem = ({ item }) => (
    <View style={styles.billCard}>
      <View style={styles.billHeader}>
        <Text style={styles.invoiceNumber}>{item.invoice_number}</Text>
        <Text style={styles.outstandingAmount}>₹{item.outstanding_amount}</Text>
      </View>
      <Text style={styles.customerName}>{item.customer_name}</Text>
      <Text style={styles.customerPhone}>{item.customer_phone}</Text>
      <View style={styles.billFooter}>
        <Text style={styles.billDate}>{item.bill_date}</Text>
        <Text style={styles.daysPending}>{item.days_pending} days pending</Text>
      </View>
      <View style={styles.paymentInfo}>
        <Text style={styles.totalAmount}>Total: ₹{item.total_amount}</Text>
        <Text style={styles.amountPaid}>Paid: ₹{item.amount_paid}</Text>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text>Loading pending payments...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Error: {error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {summary && (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Summary</Text>
          <Text style={styles.summaryText}>
            Total Pending Bills: {summary.total_pending_bills}
          </Text>
          <Text style={styles.summaryText}>
            Total Outstanding: ₹{summary.total_outstanding_amount}
          </Text>
          <Text style={styles.summaryText}>
            Credit Bills: {summary.credit_bills_count}
          </Text>
          <Text style={styles.summaryText}>
            Partial Payments: {summary.partial_payment_bills_count}
          </Text>
        </View>
      )}
      
      <FlatList
        data={pendingBills}
        renderItem={renderBillItem}
        keyExtractor={(item) => item.bill_id}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text style={styles.emptyText}>No pending payments</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center'
  },
  summaryCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8
  },
  summaryText: {
    fontSize: 14,
    marginVertical: 4
  },
  billCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3
  },
  billHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  invoiceNumber: {
    fontSize: 16,
    fontWeight: 'bold'
  },
  outstandingAmount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FF3B30'
  },
  customerName: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4
  },
  customerPhone: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8
  },
  billFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8
  },
  billDate: {
    fontSize: 12,
    color: '#666'
  },
  daysPending: {
    fontSize: 12,
    color: '#FF9500',
    fontWeight: '600'
  },
  paymentInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#eee'
  },
  totalAmount: {
    fontSize: 12,
    color: '#666'
  },
  amountPaid: {
    fontSize: 12,
    color: '#666'
  },
  errorText: {
    color: '#FF3B30',
    fontSize: 16
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginTop: 32
  }
});

export default PendingPaymentsScreen;
```

**Example 5: Python (requests):**
```python
import requests

def get_pending_payments(token, start_date=None, end_date=None):
    """
    Get pending payments and dues
    
    Args:
        token: Authentication token
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    
    Returns:
        dict: Response data with pending bills
    """
    url = 'http://localhost:8000/dashboard/dues'
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    return response.json()

# Usage
token = 'your-token-here'
data = get_pending_payments(token)

print(f"Total Pending Bills: {data['summary']['total_pending_bills']}")
print(f"Total Outstanding: ₹{data['summary']['total_outstanding_amount']}")

for bill in data['pending_bills']:
    print(f"\nInvoice: {bill['invoice_number']}")
    print(f"Customer: {bill['customer_name']}")
    print(f"Outstanding: ₹{bill['outstanding_amount']}")
    print(f"Days Pending: {bill['days_pending']}")

# Get for date range
data = get_pending_payments(token, start_date='2026-01-01', end_date='2026-01-31')
```

**Note:** 
- Pending bills include:
  - Bills with `payment_mode='credit'` (full credit, `amount_paid` typically 0)
  - Bills where `amount_paid < total_amount` (partial payment)
- Outstanding amount = `total_amount - amount_paid`
- Bills are sorted by outstanding amount (highest first)
- `days_pending` = number of days since bill date
- If `amount_paid` is `None`, it's treated as `0.00`

---

## Settings

### Push Settings

**POST** `/settings/push`

**Requires authentication + vendor approval**

Backup device-specific settings per vendor.

**Request Body:**
```json
{
  "device_id": "device-001",
  "settings_data": {
    "printer_name": "HP Printer",
    "tax_rate": 10,
    "currency": "INR",
    "theme": "dark"
  }
}
```

**Success Response (200/201):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "vendor": "550e8400-e29b-41d4-a716-446655440010",
  "device_id": "device-001",
  "settings_data": {
    "printer_name": "HP Printer",
    "tax_rate": 10,
    "currency": "INR",
    "theme": "dark"
  },
  "last_updated": "2026-01-01T10:00:00Z",
  "created_at": "2026-01-01T10:00:00Z"
}
```

---

## Error Responses

### 401 Unauthorized

**Missing or Invalid Token:**
```json
{
  "error": "Authentication required. Please login.",
  "message": "Invalid or missing token. Please login to get a valid token."
}
```

### 403 Forbidden

**Vendor Not Approved:**
```json
{
  "error": "Your vendor account is pending approval. Please wait for admin approval."
}
```

**Vendor Profile Not Found:**
```json
{
  "error": "Vendor profile not found"
}
```

### 404 Not Found

**Resource Not Found:**
```json
{
  "error": "Item not found"
}
```

or

```json
{
  "error": "Category not found"
}
```

### 400 Bad Request

**Validation Error:**
```json
{
  "error": "One or more categories not found or do not belong to vendor"
}
```

or

```json
{
  "name": ["This field is required."],
  "price": ["This field is required."]
}
```

---

## Complete Example Workflow

### 1. Register Vendor

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newvendor",
    "email": "newvendor@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "business_name": "New Business Store",
    "phone": "+1234567890",
    "gst_no": "29NEWVENDOR1234F1Z5",
    "address": "123 Main St, City, State"
  }'
```

**Note:** 
- Required fields: `username`, `email`, `password`, `password_confirm`, `business_name`, `phone`, `address`
- Optional fields: `gst_no` (can be added later via profile update)
- Use a unique username. If providing `gst_no`, it must be unique. The test vendor `vendor1` already exists - use it for login examples below.

### 2. Sales Rep or Admin Approves Vendor

**Option A: Sales Rep Interface (Recommended - Mobile Friendly)**
- Go to: `http://localhost:8000/sales-rep/`
- Login with sales rep credentials: `salesrep1` / `salesrep123`
- View pending vendors → Click "Approve" button

**Option B: Django Admin Panel**
- Go to: `http://localhost:8000/admin/`
- Login with admin credentials: `admin` / `admin123`
- Navigate to: **Vendors** section
- Select vendor(s) → Actions: "Approve selected vendors" → Go

### 3. Login and Get Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "vendor1",
    "password": "vendor123"
  }'
```

**Response:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "username": "vendor1",
  "message": "Login successful"
}
```

### 3.5. Password Reset (If Vendor Forgets Password)

**Step 1: Verify Username and GST Number**
```bash
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "username": "vendor1",
    "phone": "+919876543210"
  }'
```

**Response:**
```json
{
  "message": "Username and phone number verified. You can now reset your password.",
  "username": "vendor1",
  "phone": "+919876543210",
  "business_name": "ABC Store"
}
```

**Step 2: Reset Password**
```bash
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "username": "vendor1",
    "phone": "+919876543210",
    "new_password": "newpassword123",
    "new_password_confirm": "newpassword123"
  }'
```

**Response:**
```json
{
  "message": "Password reset successful. You can now login with your new password.",
  "username": "vendor1"
}
```

**Note:** After password reset, all existing tokens are invalidated. The vendor must login again with the new password.

### 4. Create Categories

```bash
# Create "Drinks" category
curl -X POST http://localhost:8000/items/categories/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Drinks",
    "description": "Beverages",
    "sort_order": 1
  }'

# Create "Breakfast" category
curl -X POST http://localhost:8000/items/categories/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Breakfast",
    "description": "Morning meals",
    "sort_order": 2
  }'
```

### 5. Create Item with Multiple Categories

```bash
curl -X POST http://localhost:8000/items/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Coca Cola",
    "price": "25.00",
    "stock_quantity": 100,
    "category_ids": [
      "<drinks_category_uuid>",
      "<breakfast_category_uuid>"
    ],
    "sku": "COKE-001"
  }'
```

### 6. Get Items

```bash
# Get all items
curl -X GET http://localhost:8000/items/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"

# Get items by category
curl -X GET "http://localhost:8000/items/?category=<drinks_category_uuid>" \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"

# Search items
curl -X GET "http://localhost:8000/items/?search=coke" \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

### 7. Sync Sales

```bash
curl -X POST http://localhost:8000/backup/sync \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "bill_data": {
      "bill_id": "bill-123",
      "items": [...],
      "total": 500.00
    },
    "device_id": "device-001"
  }'
```

### 8. Offline Sync Example (Mobile App Flow)

**Initial Sync (App Startup):**
```bash
# Download all categories
curl -X GET http://localhost:8000/items/categories/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"

# Download all items
curl -X GET http://localhost:8000/items/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

**Batch Sync (After Offline Changes):**
```bash
# Sync categories
curl -X POST http://localhost:8000/items/categories/sync \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "operation": "create",
      "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "New Category",
        "sort_order": 1
      },
      "timestamp": "2026-01-01T10:00:00Z"
    },
    {
      "operation": "update",
      "data": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Updated Category"
      },
      "timestamp": "2026-01-01T11:00:00Z"
    }
  ]'

# Sync items
curl -X POST http://localhost:8000/items/sync \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "operation": "create",
      "data": {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "name": "New Item",
        "price": "25.00",
        "category_ids": ["550e8400-e29b-41d4-a716-446655440000"]
      },
      "timestamp": "2026-01-01T10:00:00Z"
    }
  ]'
```

---

## Key Features

### ✅ Multi-Category Support
- Items can belong to **multiple categories**
- Use `category_ids` array when creating/updating items
- Same item can appear in "Drinks", "Breakfast", and "Lunch" simultaneously

### ✅ Vendor Isolation
- Each vendor only sees and manages their own items and categories
- Data is automatically filtered by vendor
- Vendors cannot access other vendors' data

### ✅ Offline-First Sync
- Initial sync downloads all categories and items on app startup
- All CRUD operations happen locally first
- Batch sync endpoints for syncing offline changes
- Last-Write-Wins conflict resolution based on timestamps
- Queue operations when offline, sync when internet available

### ✅ Item Images

### ✅ Inventory Management
- Raw materials inventory tracking
- Multiple unit types (kg, L, pcs, boxes, etc.)
- Stock level management with alerts
- Supplier information tracking
- Items can have images (JPG, PNG, WebP formats)
- Images stored in `media/items/{item_id}/` folder (local) or S3 bucket
- Full image URLs provided in API responses (`image_url` field)
- Mobile app can download and cache images during sync
- Images work offline after initial download
- **Storage:** Local filesystem by default, can toggle to AWS S3 (see STORAGE_CONFIGURATION.md)

### ✅ Health Check
- `GET /health/` endpoint for server monitoring
- Returns server status, database connectivity, and system stats
- No authentication required - useful for load balancers and monitoring tools

### ✅ Logging System
- Comprehensive logging for all API requests and responses
- Error logging with full stack traces
- Audit logs for vendor approvals, item changes, and business events
- Log rotation (10MB files, 5-10 backups)
- Log files: `logs/api.log`, `logs/errors.log`, `logs/audit.log`, `logs/django.log`

### ✅ Vendor Approval & Activation
- New vendors must be approved by sales rep or admin before they can use the API
- Unapproved vendors receive clear "pending approval" messages
- **Sales Rep Interface:** Mobile-friendly web UI at `/sales-rep/` for managing vendors
  - **Approve/Reject:** Controls approval status (`is_approved`)
  - **Activate/Deactivate:** Controls active status (`user.is_active`) - separate from approval
  - Both approval AND activation must be true for vendor to use the system
- **Admin Panel:** Django admin at `/admin/` for advanced vendor management
- Sales reps can approve/reject and activate/deactivate vendors individually or in bulk

### ✅ Authentication
- Token-based authentication for all endpoints
- Tokens are obtained via login
- Tokens must be included in Authorization header

---

## Notes

- **Base URL:** Replace `http://localhost:8000` with your server URL
- **UUIDs:** All IDs are UUIDs (not integers)
- **Vendor Auto-Assignment:** Vendor is automatically set from authenticated user
- **Categories:** Vendor-specific only - each vendor can only create and use their own categories (isolated)
- **Last-Write-Wins:** Item updates use timestamps for conflict resolution
- **Passive Receiver:** Sales endpoint accepts any data without validation

---

**Last Updated:** 2026-01-01

