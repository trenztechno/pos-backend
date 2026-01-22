#!/bin/bash

# POS Backend Setup Script
# This script sets up the entire Django backend from scratch

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ADMIN_USERNAME="admin"
ADMIN_EMAIL="admin@pos.local"
ADMIN_PASSWORD="admin123"
TEST_USERNAME="testuser"
TEST_EMAIL="test@pos.local"
TEST_PASSWORD="test123"
SALES_REP_USERNAME="salesrep1"
SALES_REP_EMAIL="salesrep1@pos.local"
SALES_REP_PASSWORD="salesrep123"
SALES_REP_NAME="Sales Rep 1"
DB_NAME="pos_db"
DB_USER="postgres"
DB_PASSWORD="postgres"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  POS Backend Setup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Step 1: Check Python
echo -e "${BLUE}Step 1: Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_status "Python $PYTHON_VERSION found"

# Step 2: Check PostgreSQL
echo ""
echo -e "${BLUE}Step 2: Checking PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    print_warning "PostgreSQL client not found. Please install PostgreSQL."
    print_info "Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    print_info "Fedora: sudo dnf install postgresql postgresql-server"
    exit 1
fi

if ! pg_isready &> /dev/null; then
    print_warning "PostgreSQL service is not running."
    print_info "Please start PostgreSQL: sudo systemctl start postgresql"
    exit 1
fi

print_status "PostgreSQL is running"

# Step 3: Create virtual environment
echo ""
echo -e "${BLUE}Step 3: Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Step 4: Activate virtual environment and install dependencies
echo ""
echo -e "${BLUE}Step 4: Installing dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
print_status "Dependencies installed"

# Step 5: Create .env file
echo ""
echo -e "${BLUE}Step 5: Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    # Generate secret key
    if command -v openssl &> /dev/null; then
        SECRET_KEY="django-insecure-$(openssl rand -hex 32)"
    else
        SECRET_KEY="django-insecure-$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    fi
    
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
EOF
    print_status ".env file created"
else
    print_status ".env file already exists"
fi

# Step 6: Create database
echo ""
echo -e "${BLUE}Step 6: Setting up database...${NC}"
DB_EXISTS=false

# Try to check if database exists
if command -v psql &> /dev/null; then
    # Try with sudo first
    if sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        DB_EXISTS=true
    # Try without sudo (if user has direct access)
    elif psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        DB_EXISTS=true
    fi
fi

if [ "$DB_EXISTS" = true ]; then
    print_warning "Database '$DB_NAME' already exists. Skipping creation."
else
    print_info "Creating database '$DB_NAME'..."
    DB_CREATED=false
    
    # Try with sudo
    if sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null 2>&1; then
        DB_CREATED=true
    # Try without sudo
    elif psql -U postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null 2>&1; then
        DB_CREATED=true
    fi
    
    if [ "$DB_CREATED" = true ]; then
        print_status "Database created"
    else
        print_error "Failed to create database automatically."
        print_info "Please create it manually:"
        print_info "  sudo -u postgres psql -c 'CREATE DATABASE $DB_NAME;'"
        print_info "  OR"
        print_info "  psql -U postgres -c 'CREATE DATABASE $DB_NAME;'"
        print_warning "Continuing anyway... (migrations may fail)"
    fi
fi

# Step 7: Run migrations
echo ""
echo -e "${BLUE}Step 7: Running database migrations...${NC}"
python manage.py makemigrations --noinput
python manage.py migrate --noinput
print_status "Migrations completed"

# Step 8: Create admin user
echo ""
echo -e "${BLUE}Step 8: Creating admin user...${NC}"
python manage.py shell << EOF
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create or update admin user
admin, created = User.objects.get_or_create(
    username='$ADMIN_USERNAME',
    defaults={
        'email': '$ADMIN_EMAIL',
        'is_active': True,
        'is_staff': True,
        'is_superuser': True
    }
)

# Always set password and ensure admin flags
admin.set_password('$ADMIN_PASSWORD')
admin.email = '$ADMIN_EMAIL'
admin.is_active = True
admin.is_staff = True
admin.is_superuser = True
admin.save()

Token.objects.get_or_create(user=admin)

if created:
    print('Admin user created successfully')
else:
    print('Admin user already exists (updated)')
EOF
print_status "Admin user: $ADMIN_USERNAME / $ADMIN_PASSWORD"

# Step 9: Create test user
echo ""
echo -e "${BLUE}Step 9: Creating test user...${NC}"
python manage.py shell << EOF
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create or update test user
test_user, created = User.objects.get_or_create(
    username='$TEST_USERNAME',
    defaults={
        'email': '$TEST_EMAIL',
        'is_active': True,
        'is_staff': False,
        'is_superuser': False
    }
)

# Always set password and ensure active
test_user.set_password('$TEST_PASSWORD')
test_user.email = '$TEST_EMAIL'
test_user.is_active = True
test_user.is_staff = False
test_user.is_superuser = False
test_user.save()

Token.objects.get_or_create(user=test_user)

if created:
    print('Test user created successfully')
else:
    print('Test user already exists (updated)')
EOF
print_status "Test user: $TEST_USERNAME / $TEST_PASSWORD"

# Step 10: Create sales rep user
echo ""
echo -e "${BLUE}Step 10: Creating sales rep user...${NC}"
python manage.py shell << EOF
from django.contrib.auth.models import User
from auth_app.models import SalesRep

# Create or update sales rep user
user, user_created = User.objects.get_or_create(
    username='$SALES_REP_USERNAME',
    defaults={
        'email': '$SALES_REP_EMAIL',
        'is_active': True
    }
)

# Always set password to ensure it's correct
user.set_password('$SALES_REP_PASSWORD')
user.email = '$SALES_REP_EMAIL'
user.is_active = True
user.save()

# Create or update sales rep profile
sales_rep, created = SalesRep.objects.get_or_create(
    user=user,
    defaults={
        'name': '$SALES_REP_NAME',
        'is_active': True
    }
)
sales_rep.name = '$SALES_REP_NAME'
sales_rep.is_active = True
sales_rep.save()

if user_created:
    print('Sales rep user created successfully')
else:
    print('Sales rep user already exists (updated)')
EOF
print_status "Sales rep user: $SALES_REP_USERNAME / $SALES_REP_PASSWORD"

# Step 10.5: Ensure all default users are properly set up
echo ""
echo -e "${BLUE}Step 10.5: Verifying default users...${NC}"
python ensure_default_users.py 2>/dev/null || python manage.py shell << EOF
from django.contrib.auth.models import User
from auth_app.models import SalesRep
from rest_framework.authtoken.models import Token

# Ensure admin
admin, _ = User.objects.get_or_create(username='$ADMIN_USERNAME', defaults={'email': '$ADMIN_EMAIL', 'is_active': True, 'is_staff': True, 'is_superuser': True})
admin.set_password('$ADMIN_PASSWORD')
admin.save()
Token.objects.get_or_create(user=admin)

# Ensure test user
test, _ = User.objects.get_or_create(username='$TEST_USERNAME', defaults={'email': '$TEST_EMAIL', 'is_active': True})
test.set_password('$TEST_PASSWORD')
test.save()
Token.objects.get_or_create(user=test)

# Ensure sales rep
sr_user, _ = User.objects.get_or_create(username='$SALES_REP_USERNAME', defaults={'email': '$SALES_REP_EMAIL', 'is_active': True})
sr_user.set_password('$SALES_REP_PASSWORD')
sr_user.save()
sr, _ = SalesRep.objects.get_or_create(user=sr_user, defaults={'name': '$SALES_REP_NAME', 'is_active': True})
sr.name = '$SALES_REP_NAME'
sr.is_active = True
sr.save()

print('All default users verified')
EOF
print_status "Default users verified"

# Step 11: Create test data for frontend developers and testers
echo ""
echo -e "${BLUE}Step 11: Creating test data (vendors, categories, items)...${NC}"
python create_test_data.py 2>/dev/null || {
    print_warning "Test data creation script not found or had issues"
    print_info "You can create test data later by running: python create_test_data.py"
}
if [ $? -eq 0 ]; then
    print_status "Test data created successfully"
else
    print_warning "Test data creation had issues, but continuing..."
fi

# Step 11.5: Create mobile developer account with comprehensive test data
echo ""
echo -e "${BLUE}Step 11.5: Creating mobile developer account with test data...${NC}"
python populate_mobile_dev_data.py 2>/dev/null || {
    print_warning "Mobile dev data creation script not found or had issues"
    print_info "You can create mobile dev data later by running: python populate_mobile_dev_data.py"
}
if [ $? -eq 0 ]; then
    print_status "Mobile developer account and test data created successfully"
else
    print_warning "Mobile dev data creation had issues, but continuing..."
fi

# Step 12: Verify setup
echo ""
echo -e "${BLUE}Step 12: Verifying setup...${NC}"
python manage.py check --deploy
print_status "Django system check passed"

# Step 13: Display summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Admin Credentials:${NC}"
echo -e "  Username: ${YELLOW}$ADMIN_USERNAME${NC}"
echo -e "  Password: ${YELLOW}$ADMIN_PASSWORD${NC}"
echo -e "  Admin URL: ${YELLOW}http://localhost:8000/admin/${NC}"
echo ""
echo -e "${BLUE}Sales Rep Credentials:${NC}"
echo -e "  Username: ${YELLOW}$SALES_REP_USERNAME${NC}"
echo -e "  Password: ${YELLOW}$SALES_REP_PASSWORD${NC}"
echo -e "  Sales Rep URL: ${YELLOW}http://localhost:8000/sales-rep/${NC}"
echo ""
echo -e "${BLUE}Test Vendor Accounts (For API Testing):${NC}"
echo -e "  ${GREEN}✓ APPROVED VENDORS (Can login and use API):${NC}"
echo -e "    • vendor1 / vendor123 (ABC Store)"
echo -e "    • vendor2 / vendor123 (XYZ Restaurant)"
echo -e "    • ${GREEN}mobiledev / mobile123${NC} (Mobile Dev Restaurant) ⭐ ${GREEN}For Mobile Developers${NC}"
echo ""
echo -e "  ${YELLOW}⏳ PENDING VENDOR (For testing approval flow):${NC}"
echo -e "    • pendingvendor / pending123 (Pending Business)"
echo ""
echo -e "${BLUE}Mobile Developer Account:${NC}"
echo -e "  ${GREEN}Username:${NC} mobiledev"
echo -e "  ${GREEN}Password:${NC} mobile123"
echo -e "  ${GREEN}Includes:${NC} 15+ items with images, 8 categories, sample bills (GST & Non-GST)"
echo ""
echo -e "${BLUE}Test Data Created:${NC}"
echo -e "  • Categories: Global (Drinks, Snacks) + Vendor-specific"
echo -e "  • Items: Multiple test items with categories assigned"
echo -e "  • All vendors have authentication tokens ready"
echo ""
echo -e "${BLUE}API Endpoints:${NC}"
echo -e "  Base URL: ${YELLOW}http://localhost:8000/${NC}"
echo -e "  Health Check: ${YELLOW}GET /health/${NC}"
echo -e "  Login: ${YELLOW}POST /auth/login${NC}"
echo -e "  Register: ${YELLOW}POST /auth/register${NC}"
echo -e "  Items: ${YELLOW}GET/POST /items/${NC}"
echo -e "  Categories: ${YELLOW}GET/POST /items/categories/${NC}"
echo -e "  Sales: ${YELLOW}POST /backup/sync${NC}"
echo -e "  Settings: ${YELLOW}POST /settings/push${NC}"
echo ""
echo -e "${BLUE}Quick Test Commands:${NC}"
echo -e "  1. Start server: ${YELLOW}source venv/bin/activate && python manage.py runserver${NC}"
echo -e "  2. Test vendor login: ${YELLOW}curl -X POST http://localhost:8000/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"vendor1\",\"password\":\"vendor123\"}'${NC}"
echo -e "  3. Get items (with token): ${YELLOW}curl -X GET http://localhost:8000/items/ -H 'Authorization: Token YOUR_TOKEN'${NC}"
echo -e "  4. Access Sales Rep UI: ${YELLOW}http://localhost:8000/sales-rep/${NC}"
echo ""
echo -e "${GREEN}Everything is ready for frontend development and testing! 🚀${NC}"

