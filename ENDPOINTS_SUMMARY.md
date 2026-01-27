# Complete API Endpoints Summary

**Base URL:** `http://localhost:8000` (or your server URL)

**Authentication:** Token-based authentication required for most endpoints. Include header: `Authorization: Token <your_token>`

---

## 📋 All Available Endpoints

### Health Check
- **GET** `/health/` - Server health check (No auth)

### Authentication
- **POST** `/auth/register` - Register new vendor (No auth)
  - Required fields: username, email, password, password_confirm, business_name, phone, gst_no, address
- **POST** `/auth/login` - Login and get token (No auth)
  - Returns vendor object with `logo_url` (pre-signed URL if S3 enabled)
- **GET** `/auth/profile` - Get vendor profile (Auth required)
  - Returns business details and logo URL
- **PATCH** `/auth/profile` - Update vendor profile (Auth required)
  - Use `multipart/form-data` to upload logo
  - Update business_name, phone, address, fssai_license, footer_note
- **POST** `/auth/forgot-password` - Verify GST number for password reset (No auth)
- **POST** `/auth/reset-password` - Reset password using GST number (No auth)
- **POST** `/auth/logout` - Logout (Auth required)

### Vendor Staff User Management (Owner Only, Requires Security PIN)
- **POST** `/auth/vendor/users/create` - Create staff user (Auth + PIN required)
  - Body: username, password, email (optional), security_pin
- **GET** `/auth/vendor/users` - List all vendor users (owner + staff) (Auth required)
- **POST** `/auth/vendor/users/<user_id>/reset-password` - Reset staff password (Auth + PIN required)
  - Body: new_password, security_pin
- **DELETE** `/auth/vendor/users/<user_id>` - Remove staff user (Auth + PIN required)
  - Body: security_pin

### Security PIN Management (Owner Only)
- **POST** `/auth/vendor/security-pin/set` - Set or change security PIN (Auth required)
  - Body: pin, pin_confirm (old_pin required if changing existing PIN)
- **POST** `/auth/vendor/security-pin/verify` - Verify security PIN (Auth required)
  - Body: pin (for frontend validation before showing sensitive UI)
- **GET** `/auth/vendor/security-pin/status` - Check if PIN is set (Auth required)
 - **POST** `/auth/vendor/users/create` - Create staff user under current vendor (Owner only, Auth required)
 - **GET** `/auth/vendor/users` - List all vendor users (owner + staff) (Auth required)
 - **POST** `/auth/vendor/users/<int:user_id>/reset-password` - Reset staff password (Owner only, Auth required)
 - **DELETE** `/auth/vendor/users/<int:user_id>` - Deactivate staff user (Owner only, Auth required)

### Categories (Products)
- **GET** `/items/categories/` - List all categories (Auth required)
- **POST** `/items/categories/` - Create category (Auth required)
- **GET** `/items/categories/<uuid:id>/` - Get category details (Auth required)
- **PATCH** `/items/categories/<uuid:id>/` - Update category (Auth required)
- **DELETE** `/items/categories/<uuid:id>/` - Delete category (Auth required)
- **POST** `/items/categories/sync` - Batch sync categories (Auth required)

### Items (Products)
- **GET** `/items/` - List all items (Auth required)
  - Query params: 
    - `category=<uuid>` - Filter by category
    - `search=<term>` - Search by name, description, SKU, barcode
    - `is_active=<true|false>` - Filter by active status
- **POST** `/items/` - Create item (Auth required)
  - Use `multipart/form-data` to upload images
  - Response includes `image_url` with pre-signed URL (if S3 enabled)
  - **GST Percentages:** `0.00`, `5.00`, `8.00`, `18.00`, or custom (0-100)
  - **Price Types:** `"exclusive"` (GST not included in MRP) or `"inclusive"` (GST included in MRP)
  - **Veg/Non-Veg:** `"veg"` or `"nonveg"` (optional)
  - **Item Examples:** See [API_DOCUMENTATION.md](API_DOCUMENTATION.md#complete-item-creation-examples---all-cases) for 12 complete examples
- **GET** `/items/<uuid:id>/` - Get item details (Auth required)
- **PATCH** `/items/<uuid:id>/` - Update item (Auth required)
  - Use `multipart/form-data` to update images
- **DELETE** `/items/<uuid:id>/` - Delete item (Auth required)
- **PATCH** `/items/<uuid:id>/status/` - Update item status (Auth required)
- **POST** `/items/sync` - Batch sync items (Auth required)

### Inventory Management (Raw Materials)
- **GET** `/inventory/unit-types/` - Get available unit types (No auth)
- **GET** `/inventory/` - List all inventory items (Auth required)
  - Query params: `is_active=<true|false>`, `low_stock=<true>`, `search=<term>`, `unit_type=<type>`
- **POST** `/inventory/` - Create inventory item (Auth required)
- **GET** `/inventory/<uuid:id>/` - Get inventory item details (Auth required)
- **PATCH** `/inventory/<uuid:id>/` - Update inventory item (Auth required)
- **PATCH** `/inventory/<uuid:id>/stock/` - Update stock quantity (Auth required)
  - Actions: `set`, `add`, `subtract`
- **DELETE** `/inventory/<uuid:id>/` - Delete inventory item (Auth required)

### Bills (Direct CRUD Operations)
- **GET** `/bills/` - List all bills (Auth required)
  - **Note:** All bill numbers are server-generated in format: `{prefix}-{date}-{number}`
  - Query params: 
    - `billing_mode` (`gst` or `non_gst`) - Filter by billing mode
    - `start_date` (YYYY-MM-DD) - Filter bills from this date
    - `end_date` (YYYY-MM-DD) - Filter bills until this date
    - `payment_mode` (`cash`, `upi`, `card`, `credit`, `other`) - Filter by payment mode
    - `limit` (integer, default: 100) - Maximum number of bills to return
    - `offset` (integer, default: 0) - Number of bills to skip (for pagination)
  - Returns: Paginated list of Bill objects
- **POST** `/bills/` - Create a new bill (Auth required)
  - Body: Bill object with `items_data` array
  - **Server always generates invoice number** (client cannot provide it)
  - Returns: Created Bill object with server-generated `invoice_number`
- **GET** `/bills/<uuid:id>/` - Get bill details (Auth required)
  - Returns: Bill object with nested BillItem objects
- **PATCH** `/bills/<uuid:id>/` - Update bill (Auth required)
  - Can update bill fields, items, prices, payment mode, etc.
  - Provide `items_data` array to replace all items
  - Returns: Updated Bill object
- **DELETE** `/bills/<uuid:id>/` - Delete bill (Auth required)
  - Returns: 204 No Content

### Sales Backup (Multi-Device Sync Only)
- **GET** `/backup/sync` - Download bills from server (Auth required)
  - **Purpose:** For syncing bills between devices (offline-first architecture)
  - Query params: 
    - `since` (ISO timestamp) - Get bills since this timestamp
    - `limit` (integer, default: 1000) - Maximum number of bills to return
    - `billing_mode` (`gst` or `non_gst`) - Filter by billing mode
    - `start_date` (YYYY-MM-DD) - Filter bills from this date
    - `end_date` (YYYY-MM-DD) - Filter bills until this date
  - Returns: Array of Bill objects with nested BillItem objects
- **POST** `/backup/sync` - Batch upload sales/bill data (Auth required)
  - **Purpose:** For syncing existing bills between devices (not for creating new bills)
  - **Important:** `invoice_number` is REQUIRED - this endpoint only accepts bills with existing invoice numbers
  - To create new bills, use `POST /bills/` which automatically generates invoice numbers
  - Accepts: Single bill object or array of bills
  - Format: `{ device_id, bill_data: {...} }` or `[{ device_id, bill_data: {...} }, ...]`
  - **Billing Modes:**
    - `"gst"` - GST bill (requires: cgst, sgst, igst, total_tax)
    - `"non_gst"` - Non-GST bill (no tax fields required)
  - **Payment Modes:**
    - `"cash"` - Cash payment
    - `"upi"` - UPI payment (include `payment_reference` for transaction ID)
    - `"card"` - Card payment (include `payment_reference` for card transaction ID)
    - `"credit"` - Credit payment (pending payment, `amount_paid` typically 0)
    - `"other"` - Other payment methods (wallet, cheque, etc.)
  - **Bill Examples:** See [API_DOCUMENTATION.md](API_DOCUMENTATION.md#complete-bill-creation-examples---all-cases) for 16 complete examples
  - **Note:** Use `/bills/` endpoints for direct bill creation/update. Use `/backup/sync` only for syncing between devices.

### Dashboard & Analytics
- **GET** `/dashboard/stats` - Overall dashboard statistics (Auth required)
  - Query params: `start_date` (YYYY-MM-DD, default: today), `end_date` (YYYY-MM-DD, default: today)
  - Returns: total bills, GST bills, non-GST bills, revenue, tax collected, payment split (cash/upi/card/credit/other)
- **GET** `/dashboard/sales` - Sales analytics by billing mode (Auth required)
  - Query params: 
    - `start_date` (YYYY-MM-DD, default: today)
    - `end_date` (YYYY-MM-DD, default: today)
    - `billing_mode` (`gst` or `non_gst`, default: all)
  - Returns: sales summary with daily breakdown, CGST/SGST/IGST breakdown
- **GET** `/dashboard/items` - Item sales analytics (Auth required)
  - Query params: 
    - `start_date` (YYYY-MM-DD, default: today)
    - `end_date` (YYYY-MM-DD, default: today)
    - `sort` (`most_sold` or `least_sold`, default: `most_sold`)
    - `limit` (integer, default: 10)
  - Returns: most/least sold dishes with statistics (quantity, revenue, bill count)
- **GET** `/dashboard/payments` - Payment mode analytics (Auth required)
  - Query params: `start_date` (YYYY-MM-DD, default: today), `end_date` (YYYY-MM-DD, default: today)
  - Returns: transaction split by payment mode (cash/upi/card/credit/other) with percentages
- **GET** `/dashboard/tax` - Tax collection analytics (Auth required)
  - Query params: `start_date` (YYYY-MM-DD, default: today), `end_date` (YYYY-MM-DD, default: today)
  - Returns: total tax collected with GST breakdown (CGST/SGST/IGST), tax by GST percentage
- **GET** `/dashboard/profit` - Net profit calculation (Auth required)
  - Query params: `start_date` (YYYY-MM-DD, default: today), `end_date` (YYYY-MM-DD, default: today)
  - Returns: estimated profit based on revenue and cost assumptions (60% cost, 40% profit)

### Settings
- **POST** `/settings/push` - Push device settings (Auth required)

### Sales Rep Interface (Web UI)
- **GET** `/sales-rep/` - Login page (No auth)
- **GET** `/sales-rep/vendors/` - Vendor list (Session auth)
- **GET** `/sales-rep/vendors/<uuid:vendor_id>/` - Vendor details (Session auth)
- **POST** `/sales-rep/vendors/<uuid:vendor_id>/approve/` - Approve vendor (Session auth)
- **POST** `/sales-rep/vendors/<uuid:vendor_id>/reject/` - Reject vendor (Session auth)
- **POST** `/sales-rep/vendors/bulk-approve/` - Bulk approve vendors (Session auth)

### Admin Panel
- **GET** `/admin/` - Django admin interface (Admin auth)

---

## 📊 Endpoint Statistics

- **Total Endpoints:** 47
- **No Auth Required:** 6 (health, unit-types, register, login, forgot-password, reset-password)
- **Token Auth Required:** 40 (includes 2 profile endpoints + 7 dashboard endpoints + 4 vendor user management endpoints + 5 bill CRUD endpoints + 2 sync endpoints)
- **Session Auth Required:** 5 (sales rep interface)
- **Admin Auth Required:** 1 (admin panel)

---

## 🔑 Authentication Methods

1. **Token Authentication** (Most endpoints)
   - Get token: `POST /auth/login`
   - Use header: `Authorization: Token <token>`

2. **Session Authentication** (Sales rep interface)
   - Login: `POST /sales-rep/` (form data)
   - Uses Django sessions

3. **Admin Authentication** (Admin panel)
   - Login: `GET /admin/` (Django admin login)

---

## 📚 Full Documentation

For complete API documentation with examples, see:
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete reference with examples

For mobile app integration:
- **[MOBILE_APP_GUIDE.md](MOBILE_APP_GUIDE.md)** - Step-by-step guide

For testing:
- **[TEST_ACCOUNTS.md](TEST_ACCOUNTS.md)** - Test credentials
- **[BACKEND_TESTING.md](BACKEND_TESTING.md)** - How to test endpoints
