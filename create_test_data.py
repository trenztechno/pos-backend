#!/usr/bin/env python
"""
Create test data for frontend developers and testers
Creates approved vendors, pending vendors, categories, and items
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from auth_app.models import Vendor, SalesRep
from items.models import Category, Item
from rest_framework.authtoken.models import Token
from decimal import Decimal

def create_test_vendors():
    """Create test vendors (approved and pending)"""
    print("\n📦 Creating test vendors...")
    
    # Approved Test Vendor 1
    vendor1_user, created = User.objects.get_or_create(
        username='vendor1',
        defaults={
            'email': 'vendor1@test.com',
            'first_name': 'Test',
            'last_name': 'Vendor 1',
            'is_active': True,
        }
    )
    if created:
        vendor1_user.set_password('vendor123')
        vendor1_user.save()
        print("  ✓ Created vendor1 user")
    else:
        vendor1_user.set_password('vendor123')
        vendor1_user.is_active = True
        vendor1_user.save()
        print("  ✓ Updated vendor1 user")
    
    vendor1, created = Vendor.objects.get_or_create(
        user=vendor1_user,
        defaults={
            'business_name': 'ABC Store',
            'phone': '+1234567890',
            'address': '123 Main Street, City',
            'is_approved': True,
        }
    )
    if not created:
        vendor1.is_approved = True
        vendor1.business_name = 'ABC Store'
        vendor1.save()
    vendor1_user.is_active = True
    vendor1_user.save()
    Token.objects.get_or_create(user=vendor1_user)
    print(f"  ✓ Vendor 1: vendor1 / vendor123 (APPROVED)")
    
    # Approved Test Vendor 2
    vendor2_user, created = User.objects.get_or_create(
        username='vendor2',
        defaults={
            'email': 'vendor2@test.com',
            'first_name': 'Test',
            'last_name': 'Vendor 2',
            'is_active': True,
        }
    )
    if created:
        vendor2_user.set_password('vendor123')
        vendor2_user.save()
        print("  ✓ Created vendor2 user")
    else:
        vendor2_user.set_password('vendor123')
        vendor2_user.is_active = True
        vendor2_user.save()
        print("  ✓ Updated vendor2 user")
    
    vendor2, created = Vendor.objects.get_or_create(
        user=vendor2_user,
        defaults={
            'business_name': 'XYZ Restaurant',
            'phone': '+0987654321',
            'address': '456 Oak Avenue, Town',
            'is_approved': True,
        }
    )
    if not created:
        vendor2.is_approved = True
        vendor2.business_name = 'XYZ Restaurant'
        vendor2.save()
    vendor2_user.is_active = True
    vendor2_user.save()
    Token.objects.get_or_create(user=vendor2_user)
    print(f"  ✓ Vendor 2: vendor2 / vendor123 (APPROVED)")
    
    # Pending Test Vendor (for testing approval flow)
    pending_user, created = User.objects.get_or_create(
        username='pendingvendor',
        defaults={
            'email': 'pending@test.com',
            'first_name': 'Pending',
            'last_name': 'Vendor',
            'is_active': False,
        }
    )
    if created:
        pending_user.set_password('pending123')
        pending_user.save()
        print("  ✓ Created pendingvendor user")
    else:
        pending_user.set_password('pending123')
        pending_user.is_active = False
        pending_user.save()
        print("  ✓ Updated pendingvendor user")
    
    pending_vendor, created = Vendor.objects.get_or_create(
        user=pending_user,
        defaults={
            'business_name': 'Pending Business',
            'phone': '+1111111111',
            'address': '789 Test Street',
            'is_approved': False,
        }
    )
    if not created:
        pending_vendor.is_approved = False
        pending_vendor.save()
    pending_user.is_active = False
    pending_user.save()
    print(f"  ✓ Pending Vendor: pendingvendor / pending123 (PENDING APPROVAL)")
    
    return vendor1, vendor2, pending_vendor

def create_test_categories(vendor1, vendor2):
    """Create test categories"""
    print("\n📁 Creating test categories...")
    
    # Global categories (available to all vendors)
    global_categories = [
        {'name': 'Drinks', 'description': 'Beverages and drinks', 'sort_order': 1},
        {'name': 'Snacks', 'description': 'Snacks and chips', 'sort_order': 2},
    ]
    
    for cat_data in global_categories:
        cat, created = Category.objects.get_or_create(
            name=cat_data['name'],
            vendor=None,  # Global category
            defaults=cat_data
        )
        if created:
            print(f"  ✓ Created global category: {cat_data['name']}")
        else:
            print(f"  ✓ Global category exists: {cat_data['name']}")
    
    # Vendor 1 categories
    vendor1_categories = [
        {'name': 'Breakfast', 'description': 'Breakfast items', 'sort_order': 1, 'vendor': vendor1},
        {'name': 'Lunch', 'description': 'Lunch items', 'sort_order': 2, 'vendor': vendor1},
        {'name': 'Dinner', 'description': 'Dinner items', 'sort_order': 3, 'vendor': vendor1},
    ]
    
    vendor1_cats = []
    for cat_data in vendor1_categories:
        vendor = cat_data.pop('vendor')
        cat, created = Category.objects.get_or_create(
            name=cat_data['name'],
            vendor=vendor,
            defaults=cat_data
        )
        vendor1_cats.append(cat)
        if created:
            print(f"  ✓ Created category for {vendor.business_name}: {cat_data['name']}")
        else:
            print(f"  ✓ Category exists: {cat_data['name']}")
    
    # Vendor 2 categories
    vendor2_categories = [
        {'name': 'Appetizers', 'description': 'Appetizers and starters', 'sort_order': 1, 'vendor': vendor2},
        {'name': 'Main Course', 'description': 'Main dishes', 'sort_order': 2, 'vendor': vendor2},
        {'name': 'Desserts', 'description': 'Sweet treats', 'sort_order': 3, 'vendor': vendor2},
    ]
    
    vendor2_cats = []
    for cat_data in vendor2_categories:
        vendor = cat_data.pop('vendor')
        cat, created = Category.objects.get_or_create(
            name=cat_data['name'],
            vendor=vendor,
            defaults=cat_data
        )
        vendor2_cats.append(cat)
        if created:
            print(f"  ✓ Created category for {vendor.business_name}: {cat_data['name']}")
        else:
            print(f"  ✓ Category exists: {cat_data['name']}")
    
    return vendor1_cats, vendor2_cats

def create_test_items(vendor1, vendor2, vendor1_cats, vendor2_cats):
    """Create test items"""
    print("\n🛍️ Creating test items...")
    
    # Get global categories
    drinks_cat = Category.objects.filter(name='Drinks', vendor=None).first()
    snacks_cat = Category.objects.filter(name='Snacks', vendor=None).first()
    
    # Vendor 1 items
    vendor1_items = [
        {
            'name': 'Coca Cola',
            'description': 'Cold carbonated drink',
            'price': Decimal('25.00'),
            'stock_quantity': 100,
            'sku': 'COKE-001',
            'barcode': '1234567890123',
            'is_active': True,
            'sort_order': 1,
            'categories': [drinks_cat, vendor1_cats[0]] if drinks_cat and vendor1_cats else [],
        },
        {
            'name': 'Pepsi',
            'description': 'Cold carbonated drink',
            'price': Decimal('25.00'),
            'stock_quantity': 80,
            'sku': 'PEPSI-001',
            'barcode': '1234567890124',
            'is_active': True,
            'sort_order': 2,
            'categories': [drinks_cat] if drinks_cat else [],
        },
        {
            'name': 'Sandwich',
            'description': 'Fresh sandwich',
            'price': Decimal('50.00'),
            'stock_quantity': 30,
            'sku': 'SAND-001',
            'barcode': '1234567890125',
            'is_active': True,
            'sort_order': 3,
            'categories': [vendor1_cats[0], vendor1_cats[1]] if len(vendor1_cats) >= 2 else [],
        },
        {
            'name': 'Burger',
            'description': 'Delicious burger',
            'price': Decimal('80.00'),
            'stock_quantity': 25,
            'sku': 'BURG-001',
            'barcode': '1234567890126',
            'is_active': True,
            'sort_order': 4,
            'categories': [vendor1_cats[1]] if len(vendor1_cats) >= 2 else [],
        },
    ]
    
    for item_data in vendor1_items:
        categories = item_data.pop('categories', [])
        item, created = Item.objects.get_or_create(
            name=item_data['name'],
            vendor=vendor1,
            defaults=item_data
        )
        if categories:
            item.categories.set(categories)
        if created:
            print(f"  ✓ Created item for {vendor1.business_name}: {item_data['name']}")
        else:
            print(f"  ✓ Item exists: {item_data['name']}")
    
    # Vendor 2 items
    vendor2_items = [
        {
            'name': 'Pasta',
            'description': 'Italian pasta dish',
            'price': Decimal('120.00'),
            'stock_quantity': 20,
            'sku': 'PASTA-001',
            'barcode': '2234567890123',
            'is_active': True,
            'sort_order': 1,
            'categories': [vendor2_cats[1]] if len(vendor2_cats) >= 2 else [],
        },
        {
            'name': 'Pizza',
            'description': 'Fresh pizza',
            'price': Decimal('150.00'),
            'stock_quantity': 15,
            'sku': 'PIZZA-001',
            'barcode': '2234567890124',
            'is_active': True,
            'sort_order': 2,
            'categories': [vendor2_cats[1]] if len(vendor2_cats) >= 2 else [],
        },
        {
            'name': 'Ice Cream',
            'description': 'Vanilla ice cream',
            'price': Decimal('60.00'),
            'stock_quantity': 40,
            'sku': 'ICE-001',
            'barcode': '2234567890125',
            'is_active': True,
            'sort_order': 3,
            'categories': [vendor2_cats[2]] if len(vendor2_cats) >= 3 else [],
        },
    ]
    
    for item_data in vendor2_items:
        categories = item_data.pop('categories', [])
        item, created = Item.objects.get_or_create(
            name=item_data['name'],
            vendor=vendor2,
            defaults=item_data
        )
        if categories:
            item.categories.set(categories)
        if created:
            print(f"  ✓ Created item for {vendor2.business_name}: {item_data['name']}")
        else:
            print(f"  ✓ Item exists: {item_data['name']}")

def main():
    """Create all test data"""
    print("\n" + "="*70)
    print("  CREATING TEST DATA FOR FRONTEND DEVELOPERS & TESTERS")
    print("="*70)
    
    try:
        # Create test vendors
        vendor1, vendor2, pending_vendor = create_test_vendors()
        
        # Create test categories
        vendor1_cats, vendor2_cats = create_test_categories(vendor1, vendor2)
        
        # Create test items
        create_test_items(vendor1, vendor2, vendor1_cats, vendor2_cats)
        
        print("\n" + "="*70)
        print("  ✅ TEST DATA CREATION COMPLETE")
        print("="*70)
        print("\n📋 Test Accounts Summary:")
        print("\n✅ APPROVED VENDORS (Can login and use API):")
        print("   • vendor1 / vendor123 (ABC Store)")
        print("   • vendor2 / vendor123 (XYZ Restaurant)")
        print("\n⏳ PENDING VENDOR (For testing approval flow):")
        print("   • pendingvendor / pending123 (Pending Business)")
        print("\n👨‍💼 ADMIN & SALES REP:")
        print("   • admin / admin123 (Admin)")
        print("   • salesrep1 / salesrep123 (Sales Rep)")
        print("\n📦 Test Data Created:")
        print("   • Categories: Global (Drinks, Snacks) + Vendor-specific")
        print("   • Items: Multiple items with categories assigned")
        print("   • All vendors have tokens for API testing")
        print("\n" + "="*70 + "\n")
        
        return 0
    except Exception as e:
        print(f"\n❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

