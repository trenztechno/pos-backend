#!/bin/bash
# PostgreSQL Database Setup Script

echo "Setting up PostgreSQL database for POS backend..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL is not installed. Please install it first:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  Fedora: sudo dnf install postgresql postgresql-server"
    exit 1
fi

# Check if PostgreSQL service is running
if ! pg_isready &> /dev/null; then
    echo "PostgreSQL service is not running. Starting it..."
    echo "Please run: sudo systemctl start postgresql"
    echo "Or: sudo service postgresql start"
    exit 1
fi

echo ""
echo "Creating database 'pos_db' as postgres user..."
echo "Note: This requires sudo access. You'll be prompted for your password."
echo ""

# Create database using sudo to switch to postgres user
sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname='pos_db'" | grep -q 1

if [ $? -eq 0 ]; then
    echo "Database 'pos_db' already exists!"
else
    sudo -u postgres psql -c "CREATE DATABASE pos_db;"
    if [ $? -eq 0 ]; then
        echo "✓ Database 'pos_db' created successfully!"
    else
        echo "✗ Failed to create database."
        echo ""
        echo "Alternative: Run this command manually:"
        echo "  sudo -u postgres psql -c 'CREATE DATABASE pos_db;'"
        exit 1
    fi
fi

echo ""
echo "Database setup complete!"

