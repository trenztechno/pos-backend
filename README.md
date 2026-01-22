# Offline-First Billing App - Backend Server

Django + PostgreSQL backend for the offline-first billing application.

---

## 📚 Documentation Guide

**This README is your starting point.** It points to all other documentation.

### For Mobile App Developers
1. **[MOBILE_APP_GUIDE.md](MOBILE_APP_GUIDE.md)** ⭐ **START HERE** - Complete integration guide with code examples
2. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Full API reference with all endpoints
3. **[TEST_ACCOUNTS.md](TEST_ACCOUNTS.md)** - All test credentials and accounts

### For Backend Developers
1. **[SETUP.md](SETUP.md)** - Detailed setup instructions
2. **[BACKEND_TESTING.md](BACKEND_TESTING.md)** - How to test everything
3. **[STORAGE_CONFIGURATION.md](STORAGE_CONFIGURATION.md)** - Image storage setup (Local/S3)
4. **[AUTHENTICATION_FLOW.md](AUTHENTICATION_FLOW.md)** - Auth flow details
5. **[ENDPOINTS_SUMMARY.md](ENDPOINTS_SUMMARY.md)** - Quick endpoint reference

---

## 🚀 Quick Start

**Run the automated setup script:**

```bash
./setup.sh
```

This automatically:
- ✅ Sets up virtual environment
- ✅ Installs all dependencies
- ✅ Creates database and runs migrations
- ✅ Creates admin user (`admin` / `admin123`)
- ✅ Creates sales rep user (`salesrep1` / `salesrep123`)
- ✅ Creates test vendors (approved and pending)
- ✅ **Creates mobile developer account** (`mobiledev` / `mobile123`) with comprehensive test data
- ✅ Creates test categories and items

**Mobile Developer Account (Created by setup.sh):**
- Username: `mobiledev`
- Password: `mobile123`
- Includes: 15+ items with images, 8 categories, sample bills (GST & Non-GST)

See [SETUP.md](SETUP.md) for detailed setup instructions.

---

## 🏗️ Architecture

- **Offline Authority:** Mobile device is source of truth for Sales, Server is source of truth for Inventory
- **UUIDs:** All models use UUID (v4) primary keys
- **No Sales API Latency:** Bills are saved locally first, then synced in background
- **Billing Modes:** Supports both GST and Non-GST billing modes per bill (not per vendor)
- **Structured Bill Storage:** Bills stored in relational format (Bill + BillItem models) for extendability
- **Bi-Directional Sync:** Download bills (GET /backup/sync) and upload bills (POST /backup/sync)
- **Image Storage:** Supports both local filesystem and AWS S3 storage (configurable via `USE_S3` in `.env`)

---

## 📋 Default Accounts

**Created by `setup.sh`:**

### Admin & Sales Rep
- **Admin:** `admin` / `admin123` (Django Admin: `http://localhost:8000/admin/`)
- **Sales Rep:** `salesrep1` / `salesrep123` (Sales Rep Interface: `http://localhost:8000/sales-rep/`)

### Approved Vendors (Ready to Use)
- **Vendor 1:** `vendor1` / `vendor123` (ABC Store)
- **Vendor 2:** `vendor2` / `vendor123` (XYZ Restaurant)
- **Mobile Dev:** `mobiledev` / `mobile123` ⭐ **For Mobile Developers** (Mobile Dev Restaurant)

### Pending Vendor (For Testing)
- **Pending Vendor:** `pendingvendor` / `pending123` (Pending Business)

---

## 🔑 Key API Endpoints

### Authentication
- `POST /auth/login` - Login and get token
- `POST /auth/register` - Register new vendor
- `POST /auth/logout` - Logout

### Items & Categories
- `GET /items/` - Get all items (with filters: category, search, is_active)
- `POST /items/` - Create item
- `GET /items/categories/` - Get all categories
- `POST /items/categories/` - Create category

### Sales Backup (Bi-Directional Sync)
- `GET /backup/sync` - Download bills from server (for new devices)
- `POST /backup/sync` - Upload bills to server (background sync)

### Inventory
- `GET /inventory/` - Get all inventory items
- `POST /inventory/` - Create inventory item
- `PATCH /inventory/<uuid>/stock/` - Update stock (set/add/subtract)

**See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.**

---

## 🧪 Testing

**Run comprehensive tests:**
```bash
source venv/bin/activate
python verify_all_endpoints.py
```

This tests:
- All models and fields
- All URL patterns
- Authentication system
- All API endpoints (51+ tests)
- Error handling and edge cases

**See [BACKEND_TESTING.md](BACKEND_TESTING.md) for testing guide.**

---

## 📦 Project Structure

```
pos/
├── backend/          # Django project settings
├── auth_app/         # Authentication & vendor management
├── items/            # Products/items management app
├── inventory_app/    # Raw materials inventory management
├── sales/            # Sales backup app (Bill + BillItem models)
├── settings/         # Settings backup app
├── sales_rep/        # Sales rep web interface
├── manage.py
└── requirements.txt
```

---

## ✨ Key Features

### Core Features
- **Token Authentication:** All endpoints protected with token-based authentication
- **Last-Write-Wins:** Inventory updates use timestamps for conflict resolution
- **Passive Receiver:** Sales endpoint accepts any bill data without validation
- **UUID Primary Keys:** All models use UUIDs for better offline sync
- **CORS Enabled:** Configured for mobile app access

### Advanced Features
- **Billing Modes:** Support for both GST and Non-GST billing modes per bill
- **GST Tax Details:** Full support for CGST, SGST, and IGST in GST bills
- **Structured Bill Storage:** Bills stored in relational format (Bill + BillItem models) for extendability
- **Bi-Directional Sync:** Download bills from server (GET /backup/sync) for new devices
- **Item Images:** Support for item images with local/S3 storage toggle
- **Health Check:** `/health/` endpoint for monitoring and load balancers
- **Comprehensive Logging:** API, error, and audit logging with rotation
- **Sales Rep Interface:** Mobile-friendly web UI for vendor approval
- **Multi-Category Support:** Items can belong to multiple categories
- **Offline Sync:** Batch sync endpoints for categories and items
- **Inventory Management:** Complete raw materials inventory system with 16 unit types, stock tracking, low stock alerts

---

## 📖 Documentation Files

### Essential Documentation
- **README.md** (this file) - Main guide and documentation index
- **MOBILE_APP_GUIDE.md** - Complete mobile app integration guide
- **API_DOCUMENTATION.md** - Full API reference with examples
- **TEST_ACCOUNTS.md** - All test credentials and accounts

### Setup & Configuration
- **SETUP.md** - Detailed setup instructions
- **STORAGE_CONFIGURATION.md** - Image storage setup (Local/S3)
- **AUTHENTICATION_FLOW.md** - Auth flow and backward compatibility

### Reference
- **BACKEND_TESTING.md** - Testing guide
- **ENDPOINTS_SUMMARY.md** - Quick endpoint reference

---

## 🚀 Running the Server

```bash
source venv/bin/activate
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

**Health Check:**
```bash
curl http://localhost:8000/health/
```

---

## 📞 Need Help?

- **Mobile App Integration:** See [MOBILE_APP_GUIDE.md](MOBILE_APP_GUIDE.md)
- **API Questions:** See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Setup Issues:** See [SETUP.md](SETUP.md)
- **Testing:** See [BACKEND_TESTING.md](BACKEND_TESTING.md)

---

**Last Updated:** 2026-01-22
