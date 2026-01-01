# Complete Setup Guide

## Quick Setup (Automated)

Run the setup script to automatically configure everything:

```bash
./setup.sh
```

This script will:
1. ✅ Check Python and PostgreSQL
2. ✅ Create virtual environment
3. ✅ Install all dependencies
4. ✅ Create `.env` file
5. ✅ Create PostgreSQL database
6. ✅ Run all migrations
7. ✅ Create admin user (username: `admin`, password: `admin123`)
8. ✅ Create test user (username: `testuser`, password: `test123`)
9. ✅ Verify everything works

## Manual Setup

If you prefer to set up manually or the script fails:

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Virtual environment (recommended)

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create database
sudo -u postgres psql -c "CREATE DATABASE pos_db;"

# Or if you have direct access:
psql -U postgres -c "CREATE DATABASE pos_db;"
```

### 4. Environment Configuration

Create `.env` file:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*
DB_NAME=pos_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### 5. Run Migrations

```bash
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Users

#### Admin User

```bash
python manage.py createsuperuser
```

Or use Django shell:

```python
python manage.py shell
```

```python
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create admin
admin = User.objects.create_superuser(
    username='admin',
    email='admin@pos.local',
    password='admin123'
)
Token.objects.get_or_create(user=admin)
```

#### Test User

```python
# In Django shell
test_user = User.objects.create_user(
    username='testuser',
    email='test@pos.local',
    password='test123',
    is_active=True  # Approved for testing
)
Token.objects.get_or_create(user=test_user)
```

## Default Users (Created by setup.sh)

### Admin User
- **Username:** `admin`
- **Password:** `admin123`
- **Access:** Full admin access to Django admin panel
- **URL:** `http://localhost:8000/admin/`

### Test User
- **Username:** `testuser`
- **Password:** `test123`
- **Status:** Active (approved)
- **Use:** For testing API endpoints

## Starting the Server

```bash
source venv/bin/activate
python manage.py runserver
```

Server will be available at: `http://localhost:8000/`

## Testing the Setup

### 1. Test Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123"}'
```

Expected response:
```json
{
  "token": "...",
  "user_id": 2,
  "username": "testuser",
  "message": "Login successful"
}
```

### 2. Test Protected Endpoint

```bash
# Get token from login response
TOKEN="your_token_here"

# Test items endpoint
curl -X GET http://localhost:8000/items/ \
  -H "Authorization: Token $TOKEN"
```

### 3. Test Admin Panel

1. Go to `http://localhost:8000/admin/`
2. Login with: `admin` / `admin123`
3. Check Users section to see created users

## Troubleshooting

### PostgreSQL Not Running

```bash
sudo systemctl start postgresql
# OR
sudo service postgresql start
```

### Database Creation Fails

```bash
# Check PostgreSQL is running
pg_isready

# Try creating database manually
sudo -u postgres psql
CREATE DATABASE pos_db;
\q
```

### Migration Errors

```bash
# Reset migrations (WARNING: Deletes all data)
python manage.py migrate --run-syncdb

# Or check for issues
python manage.py check
```

### Permission Errors

If you get permission errors:
1. Check PostgreSQL user permissions
2. Try using `sudo -u postgres` for database operations
3. Verify `.env` file has correct database credentials

## Project Structure

```
pos/
├── setup.sh              # Automated setup script
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (created by setup)
├── backend/              # Django project settings
├── auth_app/             # Authentication app
├── items/                # Inventory management
├── sales/                # Sales backup
└── settings/             # Settings backup
```

## Next Steps

1. ✅ Run `./setup.sh` to set up everything
2. ✅ Start server: `python manage.py runserver`
3. ✅ Test login with test user
4. ✅ Access admin panel with admin user
5. ✅ Start building your mobile app!

## Security Notes

⚠️ **Important for Production:**

- Change default admin password
- Change default test user password
- Set `DEBUG=False` in `.env`
- Use strong `SECRET_KEY`
- Configure proper `ALLOWED_HOSTS`
- Use HTTPS
- Set up proper database credentials
- Review CORS settings

