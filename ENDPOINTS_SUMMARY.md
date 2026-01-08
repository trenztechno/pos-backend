# Complete API Endpoints Summary

**Base URL:** `http://localhost:8000` (or your server URL)

**Authentication:** Token-based authentication required for most endpoints. Include header: `Authorization: Token <your_token>`

---

## 📋 All Available Endpoints

### Health Check
- **GET** `/health/` - Server health check (No auth)

### Authentication
- **POST** `/auth/register` - Register new vendor (No auth)
- **POST** `/auth/login` - Login and get token (No auth)
- **POST** `/auth/logout` - Logout (Auth required)

### Categories (Products)
- **GET** `/items/categories/` - List all categories (Auth required)
- **POST** `/items/categories/` - Create category (Auth required)
- **GET** `/items/categories/<uuid:id>/` - Get category details (Auth required)
- **PATCH** `/items/categories/<uuid:id>/` - Update category (Auth required)
- **DELETE** `/items/categories/<uuid:id>/` - Delete category (Auth required)
- **POST** `/items/categories/sync` - Batch sync categories (Auth required)

### Items (Products)
- **GET** `/items/` - List all items (Auth required)
  - Query params: `category=<uuid>`, `search=<term>`
- **POST** `/items/` - Create item (Auth required)
- **GET** `/items/<uuid:id>/` - Get item details (Auth required)
- **PATCH** `/items/<uuid:id>/` - Update item (Auth required)
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

### Sales Backup
- **POST** `/backup/sync` - Batch upload sales/bill data (Auth required)

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

- **Total Endpoints:** 27
- **No Auth Required:** 4 (health, unit-types, register, login)
- **Token Auth Required:** 22
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
