# Offline-First Billing App - Backend Server

Django + PostgreSQL backend for the offline-first billing application.

**📱 For Mobile App Developers:** 
- **🚀 [START_HERE_MOBILE.md](START_HERE_MOBILE.md)** - Quick reference
- **📖 [MOBILE_APP_GUIDE.md](MOBILE_APP_GUIDE.md)** - Complete integration guide

## Architecture

- **Offline Authority:** Mobile device is source of truth for Sales, Server is source of truth for Inventory
- **UUIDs:** All models use UUID (v4) primary keys
- **No Sales API Latency:** Bills are saved locally first, then synced in background

## Quick Start

**For new users, run the automated setup script:**

```bash
./setup.sh
```

This will automatically:
- ✅ Set up virtual environment
- ✅ Install all dependencies
- ✅ Create database
- ✅ Run migrations
- ✅ Create admin user (`admin` / `admin123`)
- ✅ Create test user (`testuser` / `test123`)
- ✅ Create sales rep user (`salesrep1` / `salesrep123`)
- ✅ Create test vendors (approved and pending)
- ✅ Create test categories and items
- ✅ Set up everything needed for frontend/testing

See [SETUP.md](SETUP.md) for detailed setup instructions and troubleshooting.

## Health Check

**Check server status:**
```bash
curl http://localhost:8000/health/
```

Returns server health, database connectivity, and system stats. No authentication required. Useful for monitoring and load balancers.

## Sales Rep Interface

**For sales representatives to approve vendors:**

Access the sales rep interface at: `http://localhost:8000/sales-rep/`

**Create a sales rep user:**
```bash
python manage.py createsalesrep salesrep1 --email salesrep1@example.com --password salesrep123 --name "John Doe"
```

**Default Sales Rep Credentials (created by setup.sh):**
- Username: `salesrep1`
- Password: `salesrep123`
- URL: `http://localhost:8000/sales-rep/`

**Features:**
- ✅ Mobile-responsive design (works on phones and tablets)
- ✅ Desktop-friendly interface
- ✅ View all vendors with approval status
- ✅ Approve/reject vendors individually or in bulk
- ✅ Search and filter vendors
- ✅ View detailed vendor information

**Test Accounts Created by Setup:**
- **Admin:** `admin` / `admin123` (Django admin access)
- **Sales Rep:** `salesrep1` / `salesrep123` (Vendor approval interface)
- **Approved Vendor 1:** `vendor1` / `vendor123` (ABC Store - can use API immediately)
- **Approved Vendor 2:** `vendor2` / `vendor123` (XYZ Restaurant - can use API immediately)
- **Pending Vendor:** `pendingvendor` / `pending123` (For testing approval flow)

**Test Data Created:**
- ✅ Categories: Global categories (Drinks, Snacks) + vendor-specific categories
- ✅ Items: Multiple test items with categories assigned
- ✅ All vendors have authentication tokens ready for API testing

**Verify Default Users:**
If login doesn't work, run this to ensure all default users are created correctly:
```bash
source venv/bin/activate
python ensure_default_users.py
```

**Recreate Test Data:**
To recreate test vendors, categories, and items:
```bash
source venv/bin/activate
python create_test_data.py
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Virtual environment (recommended)

### 2. Database Setup

**Install PostgreSQL (if not installed):**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Fedora/RHEL
sudo dnf install postgresql postgresql-server
```

**Start PostgreSQL service:**
```bash
# Ubuntu/Debian
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Or using service command
sudo service postgresql start
```

**Create database:**
```bash
# Option 1: Using createdb command
createdb pos_db

# Option 2: Using psql
psql -U postgres -c "CREATE DATABASE pos_db;"

# Option 3: Use the provided setup script
./setup_db.sh
```

**Note:** If you encounter authentication issues, you may need to configure PostgreSQL authentication or use a different user. Check your PostgreSQL configuration in `/etc/postgresql/*/main/pg_hba.conf`.

### 3. Environment Configuration

The `.env` file has been created with default values. Update it if needed:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=pos_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### 4. Install Dependencies

**Already completed!** Dependencies are installed in the virtual environment.

If you need to reinstall:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Run Migrations

**Migrations have been created!** Now run them:

```bash
source venv/bin/activate
python manage.py migrate
```

**Note:** Make sure PostgreSQL is running before running migrations.

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## API Documentation

**📖 Complete API Documentation:** See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

The API documentation includes:
- All endpoints with request/response examples
- Authentication flow
- Vendor registration and approval process
- Categories and Items (with multi-category support)
- Sales backup
- Settings
- Error responses
- Complete workflow examples

## Quick API Reference

### Authentication

- **POST /auth/register** - Register new vendor (no auth required)
- **POST /auth/login** - Login and get token (no auth required)
- **POST /auth/logout** - Logout and invalidate token (requires auth)

### Categories

- **GET /items/categories/** - Get all categories (requires auth)
- **POST /items/categories/** - Create category (requires auth)
- **GET /items/categories/<uuid>** - Get category details (requires auth)
- **PATCH /items/categories/<uuid>** - Update category (requires auth)
- **DELETE /items/categories/<uuid>** - Delete category (requires auth)

### Items

- **GET /items/** - Get all items (requires auth)
  - Query params: `category=<uuid>`, `search=<term>`
- **POST /items/** - Create item (requires auth)
  - Use `category_ids` array for multiple categories
- **GET /items/<uuid>** - Get item details (requires auth)
- **PATCH /items/<uuid>** - Update item (requires auth)
- **DELETE /items/<uuid>** - Delete item (requires auth)
- **PATCH /items/<uuid>/status** - Update item status (requires auth)

### Sales Backup

- **POST /backup/sync** - Batch sales upload (requires auth)

### Settings

- **POST /settings/push** - Push device settings (requires auth)

## Project Structure

```
pos/
├── backend/          # Django project settings
├── items/            # Inventory management app
├── sales/            # Sales backup app
├── settings/         # Settings backup app
├── manage.py
└── requirements.txt
```

## Key Features

### Core Features
- **Token Authentication:** All endpoints protected with token-based authentication
- **Last-Write-Wins:** Inventory updates use timestamps for conflict resolution
- **Passive Receiver:** Sales endpoint accepts any bill data without validation
- **UUID Primary Keys:** All models use UUIDs for better offline sync
- **CORS Enabled:** Configured for mobile app access
- **User-Friendly Errors:** Clear "Please login" messages for authentication failures

### Advanced Features
- **Item Images:** Support for item images with local/S3 storage toggle
- **Health Check:** `/health/` endpoint for monitoring and load balancers
- **Comprehensive Logging:** API, error, and audit logging with rotation
- **Sales Rep Interface:** Mobile-friendly web UI for vendor approval
- **Multi-Category Support:** Items can belong to multiple categories
- **Offline Sync:** Batch sync endpoints for categories and items

## Documentation

### 📱 For Mobile App Developers
- **🚀 [MOBILE_APP_GUIDE.md](MOBILE_APP_GUIDE.md)** - **START HERE!** Quick start guide for mobile app integration
- **📖 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference with examples
- **🧪 [TEST_ACCOUNTS.md](TEST_ACCOUNTS.md)** - Test credentials and testing scenarios

### 🔧 For Backend/Server Setup
- **🧪 [BACKEND_TESTING.md](BACKEND_TESTING.md)** - **Testing guide** - How to verify all endpoints and functionality
- **Storage Configuration:** [STORAGE_CONFIGURATION.md](STORAGE_CONFIGURATION.md) - Image storage setup (Local/S3)
- **Setup Guide:** [SETUP.md](SETUP.md) - Detailed setup instructions

### 🧪 Testing
**For backend developers:** Run `python verify_all_endpoints.py` to test all endpoints and server functionality. See [BACKEND_TESTING.md](BACKEND_TESTING.md) for details.

