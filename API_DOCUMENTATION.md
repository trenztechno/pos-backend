# Complete API Documentation

**📱 Mobile App Developers:** See [MOBILE_APP_GUIDE.md](MOBILE_APP_GUIDE.md) first for quick start guide!

**Base URL:** `http://localhost:8000` (or your server URL)

**Authentication:** All endpoints (except `/health/`, `/auth/login`, `/auth/register`, `/auth/forgot-password`, and `/auth/reset-password`) require Token Authentication.

**Billing Modes:** The system supports per-bill billing modes (not vendor-specific):
- **GST Billing** (`"gst"`): GST calculations are applied to the bill (CGST, SGST, IGST)
- **Non-GST Billing** (`"non_gst"`): No GST calculations are applied

Each bill can be either GST or Non-GST. The `billing_mode` field in the bill data determines how taxes are calculated. Vendors can create both types of bills.

---

## Table of Contents

1. [Health Check](#health-check)
2. [Authentication](#authentication)
   - [Register New Vendor](#register-new-vendor)
   - [Login](#login)
   - [Logout](#logout)
   - [Forgot Password](#forgot-password-verify-username-and-gst-number)
   - [Reset Password](#reset-password)
3. [Vendor Registration & Approval](#vendor-registration--approval)
4. [Categories](#categories)
5. [Items](#items)
6. [Inventory Management](#inventory-management)
7. [Offline Sync (Categories & Items)](#offline-sync-categories--items)
8. [Sales Backup](#sales-backup)
9. [Settings](#settings)
10. [Error Responses](#error-responses)

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
  "timestamp": "2024-01-01T10:00:00.000000+00:00",
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
  "timestamp": "2024-01-01T10:00:00.000000+00:00",
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

**Request Body (All fields required):**
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
- `gst_no`: GST number (GSTIN) (required, must be unique, used for password reset and bills)
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
    "gst_no": ["This field is required."],
    "address": ["This field is required."]
  }
}
```

**Example (cURL):**
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

**Note:** Use a unique username and GST number. The test vendor `vendor1` already exists - use it for login, not registration. Billing mode (GST/Non-GST) is set per bill, not during registration.

---

### Login

**POST** `/auth/login`

**No authentication required**

Login to get an authentication token. Only approved vendors can login.

**Request Body:**
```json
{
  "username": "vendor1",
  "password": "vendor123"
}
```

**Success Response (200):**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "username": "vendor1",
  "message": "Login successful",
  "vendor": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "ABC Restaurant",
    "gst_no": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "logo_url": "http://localhost:8000/media/vendors/vendor-id/logo.png",
    "footer_note": "Thank you for visiting!"
  }
}
```

**Note:** The `vendor` object is only included for vendor accounts. It contains:
- `logo_url`: URL to restaurant logo (null if not uploaded)
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

### Forgot Password (Verify Username and GST Number)

**POST** `/auth/forgot-password`

**No authentication required**

Verifies the username and GST number to initiate password reset flow. This is the first step in password reset. Both username and GST number must match the same vendor account.

**Request Body:**
```json
{
  "username": "vendor1",
  "gst_no": "29ABCDE1234F1Z5"
}
```

**Field Descriptions:**
- `username`: Username of the vendor account (required)
- `gst_no`: GST number of the vendor account (required, must match the username)

**Success Response (200):**
```json
{
  "message": "Username and GST number verified. You can now reset your password.",
  "username": "vendor1",
  "gst_no": "29ABCDE1234F1Z5",
  "business_name": "ABC Store"
}
```

**Error Responses:**

**Username Not Found (400):**
```json
{
  "error": "Username and GST number verification failed",
  "details": {
    "non_field_errors": ["Username not found. Please check and try again."]
  }
}
```

**Username and GST Don't Match (400):**
```json
{
  "error": "Username and GST number verification failed",
  "details": {
    "non_field_errors": ["Username and GST number do not match."]
  }
}
```

**Account Pending Approval (400):**
```json
{
  "error": "Username and GST number verification failed",
  "details": {
    "non_field_errors": ["Your vendor account is pending approval. Please contact admin."]
  }
}
```

**Account Inactive (400):**
```json
{
  "error": "Username and GST number verification failed",
  "details": {
    "non_field_errors": ["Your account is inactive. Please contact admin."]
  }
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"username": "vendor1", "gst_no": "29ABCDE1234F1Z5"}'
```

---

### Reset Password

**POST** `/auth/reset-password`

**No authentication required**

Resets the password for a vendor account using their username and GST number. This is the second step after verifying username and GST number.

**Request Body:**
```json
{
  "username": "vendor1",
  "gst_no": "29ABCDE1234F1Z5",
  "new_password": "newpassword123",
  "new_password_confirm": "newpassword123"
}
```

**Field Descriptions:**
- `username`: Username of the vendor account (required, must match forgot-password step)
- `gst_no`: GST number (required, must match the username and forgot-password step)
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

**Username and GST Don't Match (400):**
```json
{
  "error": "Password reset failed",
  "details": {
    "non_field_errors": ["Username and GST number do not match."]
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
    "gst_no": "29ABCDE1234F1Z5",
    "new_password": "newpassword123",
    "new_password_confirm": "newpassword123"
  }'
```

**Password Reset Flow:**
1. User forgets password
2. User enters username and GST number → `POST /auth/forgot-password`
3. System verifies username and GST number match and returns confirmation
4. User enters new password with username and GST → `POST /auth/reset-password`
5. Password is reset, all existing tokens are invalidated
6. User can now login with new password

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
   - **Required fields:** `username`, `email`, `password`, `password_confirm`, `business_name`, `phone`, `gst_no`, `address`
   - Creates User account (inactive)
   - Creates Vendor profile (not approved, with GST number)
   - Returns: "Registration successful. Your account is pending approval."
   - **Note:** GST number is required and must be unique. It will be used for password reset.

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
- ✅ View all vendors with approval status
- ✅ Approve/reject vendors individually or in bulk
- ✅ Search and filter vendors
- ✅ View detailed vendor information
- ✅ Statistics dashboard (pending/approved counts)

**How to Use:**
1. Login with sales rep credentials
2. View pending vendors (filter by "Pending" status)
3. Click "Approve" button on vendor card/row
4. Or select multiple vendors and use "Bulk Approve"

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

Categories organize items. Each vendor can create their own categories, and there are also global categories available to all vendors.

### Get All Categories

**GET** `/items/categories/`

**Requires authentication + vendor approval**

Returns all categories available to the vendor (vendor-specific + global categories).

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
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Breakfast",
    "description": "Morning meals",
    "is_active": true,
    "sort_order": 2,
    "item_count": 3,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
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
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
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
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
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
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T11:00:00Z"
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
    "last_updated": "2024-01-01T10:00:00Z",
    "created_at": "2024-01-01T10:00:00Z"
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
  "gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "additional_discount": "0.00",
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
- `gst_percentage`: GST percentage - 0%, 5%, 8%, 18%, or custom (optional, not compulsory for item creation)
- `veg_nonveg`: `"veg"` or `"nonveg"` (optional)
- `additional_discount`: Additional discount amount (optional, default: 0)
- `category_ids`: Array of category UUIDs (breakfast, lunch, dinner, snacks, beverage, desserts, etc.)
- `image`: Item image file (optional - item name shown if no image)

**Note:** 
- `category_ids` is an array - items can belong to multiple categories!
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
  "gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "additional_discount": "0.00",
  "stock_quantity": 100,
  "sku": "COKE-001",
  "barcode": "1234567890123",
  "is_active": true,
  "sort_order": 1,
  "vendor_name": "ABC Restaurant",
  "image": null,
  "image_url": null,
  "last_updated": "2024-01-01T10:00:00Z",
  "created_at": "2024-01-01T10:00:00Z"
}
```

**Note:** Items can include images. Use `multipart/form-data` when uploading images:
```bash
curl -X POST http://localhost:8000/items/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "name=Coca Cola" \
  -F "price=25.00" \
  -F "image=@/path/to/image.jpg"
```

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
  "gst_percentage": "18.00",
  "veg_nonveg": "veg",
  "additional_discount": "0.00",
  "stock_quantity": 100,
  "sku": "COKE-001",
  "barcode": "1234567890123",
  "is_active": true,
  "sort_order": 1,
  "vendor_name": "ABC Restaurant",
  "image": "items/660e8400-e29b-41d4-a716-446655440000/660e8400-e29b-41d4-a716-446655440000.jpg",
  "image_url": "http://localhost:8000/media/items/660e8400-e29b-41d4-a716-446655440000/660e8400-e29b-41d4-a716-446655440000.jpg",
  "last_updated": "2024-01-01T10:00:00Z",
  "created_at": "2024-01-01T10:00:00Z"
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

**Request Body (partial update):**
```json
{
  "price": "30.00",
  "stock_quantity": 150,
  "category_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440002"
  ]
}
```

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
  "image_url": "http://localhost:8000/media/items/660e8400-e29b-41d4-a716-446655440000/660e8400-e29b-41d4-a716-446655440000.jpg",
  "last_updated": "2024-01-01T11:00:00Z",
  "created_at": "2024-01-01T10:00:00Z"
}
```

**Note:** To update an image, use `multipart/form-data` and include the `image` field in the request.

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
    "updated_at": "2024-01-01T10:00:00Z"
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
    "updated_at": "2024-01-01T10:00:00Z"
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
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
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
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
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
  "last_restocked_at": "2024-01-01T11:00:00Z",
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

## Offline Sync (Categories & Items)

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
    "timestamp": "2024-01-01T10:00:00Z"
  },
  {
    "operation": "update",
    "data": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Updated Category"
    },
    "timestamp": "2024-01-01T11:00:00Z"
  },
  {
    "operation": "delete",
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "timestamp": "2024-01-01T12:00:00Z"
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
    "timestamp": "2024-01-01T10:00:00Z"
  },
  {
    "operation": "update",
    "data": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "price": "30.00",
      "stock_quantity": 150
    },
    "timestamp": "2024-01-01T11:00:00Z"
  },
  {
    "operation": "delete",
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "timestamp": "2024-01-01T12:00:00Z"
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
      "image_url": "http://localhost:8000/media/items/...",
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

## Sales Backup

### Download Sales Data (GET)

**GET** `/backup/sync`

**Requires authentication + vendor approval**

Download bills from the server. This is used when a new device logs in with the same tenant to load existing sales history.

**Query Parameters:**
- `since` (optional): ISO timestamp - Only get bills synced after this time (e.g., `2024-01-01T10:00:00Z`)
- `limit` (optional, default=1000): Maximum number of bills to return
- `billing_mode` (optional): Filter by billing mode (`gst` or `non_gst`)
- `start_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2024-01-01`)
- `end_date` (optional): Filter by bill date - YYYY-MM-DD format (e.g., `2024-01-31`)

**Success Response (200):**
```json
{
  "count": 2,
  "vendor_id": "vendor-uuid",
  "vendor_name": "ABC Restaurant",
  "bills": [
    {
      "id": "bill-uuid-1",
      "invoice_number": "INV-2024-001",
      "bill_number": "BN-2024-001",
      "bill_date": "2024-01-01",
      "billing_mode": "gst",
      "restaurant_name": "ABC Restaurant",
      "address": "123 Main St",
      "gstin": "29ABCDE1234F1Z5",
      "fssai_license": "12345678901234",
      "logo_url": "http://localhost:8000/media/vendors/.../logo.png",
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
          "gst_percentage": "18.00",
          "item_gst_amount": "36.00",
          "veg_nonveg": "veg"
        }
      ],
      "item_count": 1,
      "total_quantity": 2.0,
      "created_at": "2024-01-01T10:00:00Z",
      "synced_at": "2024-01-01T10:00:00Z"
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
curl -X GET "http://localhost:8000/backup/sync?since=2024-01-01T00:00:00Z&limit=100" \
  -H "Authorization: Token <token>"

# Get bills for a date range
curl -X GET "http://localhost:8000/backup/sync?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Token <token>"
```

---

### Upload Sales Data (POST)

**POST** `/backup/sync`

**Requires authentication + vendor approval**

Batch upload sales/bill data. Accepts single bill or array of bills. Server acts as passive receiver - no validation. Bills are stored in a structured, extendable format (Bill and BillItem models) for future business logic.

**Request Body (Single Bill):**

**GST Bill Example (Complete Format):**
```json
{
  "bill_data": {
    "invoice_number": "INV-2024-001",
    "bill_id": "bill-123",
    "billing_mode": "gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "logo_url": "http://localhost:8000/media/vendors/vendor-id/logo.png",
    "bill_number": "BN-2024-001",
    "bill_date": "2024-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Product A",
        "price": 100.00,
        "mrp_price": 100.00,
        "price_type": "exclusive",
        "gst_percentage": 18.00,
        "quantity": 2,
        "subtotal": 200.00,
        "item_gst": 36.00
      }
    ],
    "subtotal": 200.00,
    "cgst": 18.00,
    "sgst": 18.00,
    "igst": 0.00,
    "total_tax": 36.00,
    "total": 236.00,
    "footer_note": "Thank you for visiting!",
    "timestamp": "2024-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Non-GST Bill Example (Complete Format):**
```json
{
  "bill_data": {
    "invoice_number": "INV-2024-002",
    "bill_id": "bill-124",
    "billing_mode": "non_gst",
    "restaurant_name": "ABC Restaurant",
    "address": "123 Main St, City, State",
    "gstin": "29ABCDE1234F1Z5",
    "fssai_license": "12345678901234",
    "logo_url": "http://localhost:8000/media/vendors/vendor-id/logo.png",
    "bill_number": "BN-2024-002",
    "bill_date": "2024-01-01",
    "items": [
      {
        "id": "item-uuid-1",
        "name": "Product B",
        "price": 150.00,
        "mrp_price": 150.00,
        "quantity": 1,
        "subtotal": 150.00
      }
    ],
    "subtotal": 150.00,
    "total": 150.00,
    "footer_note": "Thank you for visiting!",
    "timestamp": "2024-01-01T10:00:00Z"
  },
  "device_id": "device-001"
}
```

**Bill Data Structure (Complete):**

**Required Fields (All Bills):**
- `invoice_number`: Auto-generated invoice number (sequential, syncs with GST and non-GST bills)
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
- `cgst`: Central GST amount (required for intra-state)
- `sgst`: State GST amount (required for intra-state)
- `igst`: Integrated GST amount (required for inter-state, 0 for intra-state)
- `total_tax`: Sum of all taxes (cgst + sgst + igst)

**For Non-GST Bills (`billing_mode: "non_gst"`):**
- No tax fields required
- `total` should equal `subtotal`
- Product GST should NOT be added to totaling bill

**Item Structure in Bills:**
- `id`: Item UUID
- `name`: Item name
- `price`: Base price
- `mrp_price`: MRP price (exclusive or inclusive based on price_type)
- `price_type`: `"exclusive"` or `"inclusive"` (GST calculation mode)
- `gst_percentage`: GST percentage for this item (0%, 5%, 8%, 18%, or custom)
- `quantity`: Quantity purchased
- `subtotal`: Item subtotal (mrp_price * quantity)
- `item_gst`: GST amount for this item (only for GST bills)

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
      "invoice_number": "INV-2024-001",
      "bill_number": "BN-2024-001",
      "bill_date": "2024-01-01",
      "billing_mode": "gst",
      "restaurant_name": "ABC Restaurant",
      "address": "123 Main St",
      "gstin": "29ABCDE1234F1Z5",
      "fssai_license": "12345678901234",
      "logo_url": "http://localhost:8000/media/vendors/.../logo.png",
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
          "gst_percentage": "18.00",
          "item_gst_amount": "36.00",
          "veg_nonveg": "veg"
        }
      ],
      "item_count": 1,
      "total_quantity": 2.0,
      "created_at": "2024-01-01T10:00:00Z",
      "synced_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    },
    ...
  ],
  "errors": []  // Only present if some bills failed to sync
}
```

**Note:** Bills are now stored in a structured, relational format (Bill and BillItem models) instead of JSON blobs. This makes the system fully extendable for future business logic like:
- Analytics and reporting (e.g., "Show top 5 selling items")
- Inventory deduction (automatically reduce stock when bill is created)
- Tax reporting (e.g., "Calculate total CGST payable for March")
- Customer loyalty programs
- Advanced filtering and querying

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
  "last_updated": "2024-01-01T10:00:00Z",
  "created_at": "2024-01-01T10:00:00Z"
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
- All fields are required: `username`, `email`, `password`, `password_confirm`, `business_name`, `phone`, `gst_no`, and `address`.
- Use a unique username and GST number. The test vendor `vendor1` already exists - use it for login examples below.

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
    "gst_no": "29ABCDE1234F1Z5"
  }'
```

**Response:**
```json
{
  "message": "Username and GST number verified. You can now reset your password.",
  "username": "vendor1",
  "gst_no": "29ABCDE1234F1Z5",
  "business_name": "ABC Store"
}
```

**Step 2: Reset Password**
```bash
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "username": "vendor1",
    "gst_no": "29ABCDE1234F1Z5",
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
      "timestamp": "2024-01-01T10:00:00Z"
    },
    {
      "operation": "update",
      "data": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Updated Category"
      },
      "timestamp": "2024-01-01T11:00:00Z"
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
      "timestamp": "2024-01-01T10:00:00Z"
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

### ✅ Vendor Approval
- New vendors must be approved by sales rep or admin before they can use the API
- Unapproved vendors receive clear "pending approval" messages
- **Sales Rep Interface:** Mobile-friendly web UI at `/sales-rep/` for approving vendors
- **Admin Panel:** Django admin at `/admin/` for advanced vendor management
- Sales reps can approve/reject vendors individually or in bulk

### ✅ Authentication
- Token-based authentication for all endpoints
- Tokens are obtained via login
- Tokens must be included in Authorization header

---

## Notes

- **Base URL:** Replace `http://localhost:8000` with your server URL
- **UUIDs:** All IDs are UUIDs (not integers)
- **Vendor Auto-Assignment:** Vendor is automatically set from authenticated user
- **Categories:** Can be vendor-specific or global (vendor=null)
- **Last-Write-Wins:** Item updates use timestamps for conflict resolution
- **Passive Receiver:** Sales endpoint accepts any data without validation

---

**Last Updated:** 2024-01-01

