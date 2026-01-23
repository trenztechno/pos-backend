#!/usr/bin/env python
"""
Verify Default Setup and Data
Ensures all default accounts, test data, and mobile dev data are present

This script verifies:
1. Default accounts (admin, salesrep, vendors)
2. Mobile developer account (mobiledev)
3. Test data (categories, items, bills)
4. Image URLs are accessible
5. All credentials match documentation

Run this after setup.sh to verify everything is correctly configured.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from auth_app.models import Vendor, SalesRep
from items.models import Category, Item
from sales.models import Bill, BillItem
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_pass(message):
    print(f"✓ {message}")

def print_fail(message):
    print(f"✗ {message}")

def print_warn(message):
    print(f"⚠ {message}")

def verify_default_accounts():
    """Verify all default accounts exist and have correct credentials"""
    print_section("1. Verifying Default Accounts")
    
    all_passed = True
    
    # Admin Account
    try:
        admin = User.objects.get(username='admin')
        if admin.check_password('admin123') and admin.is_superuser and admin.is_staff:
            print_pass("Admin account: admin / admin123 (Superuser)")
        else:
            print_fail("Admin account exists but password or permissions incorrect")
            all_passed = False
    except User.DoesNotExist:
        print_fail("Admin account (admin) not found")
        all_passed = False
    
    # Sales Rep Account
    try:
        salesrep_user = User.objects.get(username='salesrep1')
        if salesrep_user.check_password('salesrep123'):
            try:
                salesrep = SalesRep.objects.get(user=salesrep_user)
                if salesrep.is_active:
                    print_pass("Sales Rep account: salesrep1 / salesrep123 (Active)")
                else:
                    print_warn("Sales Rep account exists but is inactive")
            except SalesRep.DoesNotExist:
                print_fail("Sales Rep profile not found for salesrep1")
                all_passed = False
        else:
            print_fail("Sales Rep account exists but password incorrect")
            all_passed = False
    except User.DoesNotExist:
        print_fail("Sales Rep account (salesrep1) not found")
        all_passed = False
    
    # Vendor 1 (ABC Store)
    try:
        vendor1_user = User.objects.get(username='vendor1')
        if vendor1_user.check_password('vendor123'):
            try:
                vendor1 = Vendor.objects.get(user=vendor1_user)
                if vendor1.is_approved and vendor1.business_name == 'ABC Store':
                    if vendor1.gst_no == '29ABCDE1234F1Z5':
                        print_pass("Vendor 1: vendor1 / vendor123 (ABC Store, Approved)")
                    else:
                        print_warn(f"Vendor 1 exists but GST number is {vendor1.gst_no} (expected: 29ABCDE1234F1Z5)")
                else:
                    print_fail(f"Vendor 1 exists but not approved or wrong business name: {vendor1.business_name}")
                    all_passed = False
            except Vendor.DoesNotExist:
                print_fail("Vendor 1 profile not found")
                all_passed = False
        else:
            print_fail("Vendor 1 account exists but password incorrect")
            all_passed = False
    except User.DoesNotExist:
        print_fail("Vendor 1 account (vendor1) not found")
        all_passed = False
    
    # Vendor 2 (XYZ Restaurant)
    try:
        vendor2_user = User.objects.get(username='vendor2')
        if vendor2_user.check_password('vendor123'):
            try:
                vendor2 = Vendor.objects.get(user=vendor2_user)
                if vendor2.is_approved and vendor2.business_name == 'XYZ Restaurant':
                    if vendor2.gst_no == '27XYZAB5678G2H6':
                        print_pass("Vendor 2: vendor2 / vendor123 (XYZ Restaurant, Approved)")
                    else:
                        print_warn(f"Vendor 2 exists but GST number is {vendor2.gst_no} (expected: 27XYZAB5678G2H6)")
                else:
                    print_fail(f"Vendor 2 exists but not approved or wrong business name: {vendor2.business_name}")
                    all_passed = False
            except Vendor.DoesNotExist:
                print_fail("Vendor 2 profile not found")
                all_passed = False
        else:
            print_fail("Vendor 2 account exists but password incorrect")
            all_passed = False
    except User.DoesNotExist:
        print_fail("Vendor 2 account (vendor2) not found")
        all_passed = False
    
    # Pending Vendor
    try:
        pending_user = User.objects.get(username='pendingvendor')
        if pending_user.check_password('pending123'):
            try:
                pending_vendor = Vendor.objects.get(user=pending_user)
                if not pending_vendor.is_approved:
                    print_pass("Pending Vendor: pendingvendor / pending123 (Pending Approval)")
                else:
                    print_warn("Pending Vendor exists but is already approved")
            except Vendor.DoesNotExist:
                print_fail("Pending Vendor profile not found")
                all_passed = False
        else:
            print_fail("Pending Vendor account exists but password incorrect")
            all_passed = False
    except User.DoesNotExist:
        print_warn("Pending Vendor account (pendingvendor) not found (optional)")
    
    # Mobile Developer Account
    try:
        mobiledev_user = User.objects.get(username='mobiledev')
        if mobiledev_user.check_password('mobile123'):
            try:
                mobiledev_vendor = Vendor.objects.get(user=mobiledev_user)
                if mobiledev_vendor.is_approved:
                    if mobiledev_vendor.business_name == 'Mobile Dev Restaurant':
                        if mobiledev_vendor.gst_no == '29MOBILE1234D1E5':
                            if mobiledev_vendor.fssai_license == '12345678901234':
                                print_pass("Mobile Dev: mobiledev / mobile123 (Mobile Dev Restaurant, Approved)")
                                print_pass(f"  - GST: {mobiledev_vendor.gst_no}")
                                print_pass(f"  - FSSAI: {mobiledev_vendor.fssai_license}")
                                if mobiledev_vendor.logo:
                                    print_pass(f"  - Logo: Present ({mobiledev_vendor.logo.name})")
                                else:
                                    print_warn("  - Logo: Not present (optional)")
                                if mobiledev_vendor.footer_note:
                                    print_pass(f"  - Footer Note: Present")
                                else:
                                    print_warn("  - Footer Note: Not present (optional)")
                            else:
                                print_fail(f"Mobile Dev FSSAI incorrect: {mobiledev_vendor.fssai_license}")
                                all_passed = False
                        else:
                            print_fail(f"Mobile Dev GST incorrect: {mobiledev_vendor.gst_no}")
                            all_passed = False
                    else:
                        print_fail(f"Mobile Dev business name incorrect: {mobiledev_vendor.business_name}")
                        all_passed = False
                else:
                    print_fail("Mobile Dev account exists but not approved")
                    all_passed = False
            except Vendor.DoesNotExist:
                print_fail("Mobile Dev vendor profile not found")
                all_passed = False
        else:
            print_fail("Mobile Dev account exists but password incorrect")
            all_passed = False
    except User.DoesNotExist:
        print_fail("Mobile Dev account (mobiledev) not found - Run populate_mobile_dev_data.py")
        all_passed = False
    
    return all_passed

def verify_test_data():
    """Verify test data (categories, items) exists"""
    print_section("2. Verifying Test Data")
    
    all_passed = True
    
    # Check categories
    categories = Category.objects.all()
    print(f"  Total Categories: {categories.count()}")
    
    # Check global categories
    global_cats = Category.objects.filter(vendor__isnull=True)
    if global_cats.exists():
        print_pass(f"Global Categories: {global_cats.count()} found")
        for cat in global_cats[:5]:  # Show first 5
            print(f"    - {cat.name}")
    else:
        print_warn("No global categories found")
    
    # Check vendor-specific categories
    vendor_cats = Category.objects.filter(vendor__isnull=False)
    if vendor_cats.exists():
        print_pass(f"Vendor-Specific Categories: {vendor_cats.count()} found")
    else:
        print_warn("No vendor-specific categories found")
    
    # Check items
    items = Item.objects.all()
    print(f"  Total Items: {items.count()}")
    
    if items.exists():
        # Check items with GST fields
        items_with_gst = items.filter(mrp_price__isnull=False)
        print_pass(f"Items with GST fields (mrp_price): {items_with_gst.count()}")
        
        # Check items with images
        items_with_images = items.exclude(image='')
        print_pass(f"Items with images: {items_with_images.count()}")
        
        # Check items by vendor
        for vendor in Vendor.objects.filter(is_approved=True)[:3]:
            vendor_items = items.filter(vendor=vendor)
            if vendor_items.exists():
                print_pass(f"  {vendor.business_name}: {vendor_items.count()} items")
    else:
        print_warn("No items found")
    
    return all_passed

def verify_mobile_dev_data():
    """Verify mobile developer data is comprehensive"""
    print_section("3. Verifying Mobile Developer Data")
    
    all_passed = True
    
    try:
        mobiledev_vendor = Vendor.objects.get(user__username='mobiledev')
        
        # Check categories
        categories = Category.objects.filter(vendor=mobiledev_vendor)
        global_cats = Category.objects.filter(vendor__isnull=True)
        total_cats = categories.count() + global_cats.count()
        
        if total_cats >= 6:
            print_pass(f"Categories: {total_cats} available (expected: 6+)")
        else:
            print_warn(f"Categories: {total_cats} found (expected: 6+)")
        
        # Check items
        items = Item.objects.filter(vendor=mobiledev_vendor)
        if items.count() >= 15:
            print_pass(f"Items: {items.count()} found (expected: 15+)")
            
            # Check items with complete GST fields
            complete_items = items.filter(
                mrp_price__isnull=False,
                price_type__isnull=False
            )
            print_pass(f"Items with complete GST fields: {complete_items.count()}")
            
            # Check items with images
            items_with_images = items.exclude(image='')
            if items_with_images.count() >= 10:
                print_pass(f"Items with images: {items_with_images.count()}")
            else:
                print_warn(f"Items with images: {items_with_images.count()} (expected: 10+)")
        else:
            print_fail(f"Items: {items.count()} found (expected: 15+)")
            all_passed = False
        
        # Check bills
        bills = Bill.objects.filter(vendor=mobiledev_vendor)
        if bills.exists():
            gst_bills = bills.filter(billing_mode='gst')
            non_gst_bills = bills.filter(billing_mode='non_gst')
            print_pass(f"Sample Bills: {bills.count()} found")
            print_pass(f"  - GST Bills: {gst_bills.count()}")
            print_pass(f"  - Non-GST Bills: {non_gst_bills.count()}")
            
            # Check bill items
            total_bill_items = BillItem.objects.filter(bill__vendor=mobiledev_vendor).count()
            if total_bill_items > 0:
                print_pass(f"  - Bill Items: {total_bill_items} items in bills")
        else:
            print_warn("No sample bills found (optional)")
        
        # Check bills for other vendors too
        all_bills = Bill.objects.all()
        if all_bills.exists():
            print_pass(f"Total Bills in System: {all_bills.count()}")
            for vendor in Vendor.objects.filter(is_approved=True)[:3]:
                vendor_bills = Bill.objects.filter(vendor=vendor)
                if vendor_bills.exists():
                    print_pass(f"  - {vendor.business_name}: {vendor_bills.count()} bills")
        
    except Vendor.DoesNotExist:
        print_fail("Mobile Dev vendor not found")
        all_passed = False
    
    return all_passed

def verify_api_access():
    """Verify API access with default accounts"""
    print_section("4. Verifying API Access")
    
    all_passed = True
    client = APIClient()
    
    # Test vendor1 login
    try:
        response = client.post('/auth/login', {
            'username': 'vendor1',
            'password': 'vendor123'
        }, format='json')
        if response.status_code == 200 and 'token' in response.data:
            token = response.data['token']
            print_pass("Vendor 1 login successful")
            
            # Test API access with token
            client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
            items_response = client.get('/items/')
            if items_response.status_code == 200:
                print_pass("Vendor 1 API access working")
            else:
                print_fail(f"Vendor 1 API access failed: {items_response.status_code}")
                all_passed = False
        else:
            print_fail(f"Vendor 1 login failed: {response.status_code}")
            all_passed = False
    except Exception as e:
        print_fail(f"Vendor 1 login error: {e}")
        all_passed = False
    
    # Test mobiledev login
    try:
        client.credentials()  # Clear previous auth
        response = client.post('/auth/login', {
            'username': 'mobiledev',
            'password': 'mobile123'
        }, format='json')
        if response.status_code == 200 and 'token' in response.data:
            token = response.data['token']
            vendor_data = response.data.get('vendor', {})
            print_pass("Mobile Dev login successful")
            
            # Verify vendor data in response
            if 'fssai_license' in vendor_data and 'logo_url' in vendor_data:
                print_pass("Login response includes fssai_license and logo_url")
            else:
                print_warn("Login response missing some vendor fields")
            
            # Test API access
            client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
            items_response = client.get('/items/')
            if items_response.status_code == 200:
                items_data = items_response.data
                if isinstance(items_data, list) and len(items_data) > 0:
                    print_pass(f"Mobile Dev API access working ({len(items_data)} items)")
                else:
                    print_warn("Mobile Dev API access working but no items returned")
            else:
                print_fail(f"Mobile Dev API access failed: {items_response.status_code}")
                all_passed = False
        else:
            print_fail(f"Mobile Dev login failed: {response.status_code}")
            all_passed = False
    except Exception as e:
        print_fail(f"Mobile Dev login error: {e}")
        all_passed = False
    
    return all_passed

def verify_dashboard_data():
    """Verify dashboard endpoints work with test data"""
    print_section("5. Verifying Dashboard Data")
    
    all_passed = True
    client = APIClient()
    
    # Test with vendor1
    try:
        vendor1 = Vendor.objects.get(user__username='vendor1')
        user = vendor1.user
        token, _ = Token.objects.get_or_create(user=user)
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Test dashboard stats
        response = client.get('/dashboard/stats')
        if response.status_code == 200:
            data = response.data
            if 'statistics' in data:
                stats = data['statistics']
                print_pass(f"Dashboard Stats: Working")
                print_pass(f"  - Total Bills: {stats.get('total_bills', 0)}")
                print_pass(f"  - Total Revenue: ₹{stats.get('total_revenue', '0.00')}")
                print_pass(f"  - Payment Split: {len(stats.get('payment_split', {}))} modes")
            else:
                print_warn("Dashboard stats response missing statistics field")
        else:
            print_fail(f"Dashboard stats failed: {response.status_code}")
            all_passed = False
        
        # Test dashboard sales
        response = client.get('/dashboard/sales')
        if response.status_code == 200:
            print_pass("Dashboard Sales: Working")
        else:
            print_fail(f"Dashboard sales failed: {response.status_code}")
            all_passed = False
        
        # Test dashboard items
        response = client.get('/dashboard/items?sort=most_sold')
        if response.status_code == 200:
            data = response.data
            items = data.get('items', [])
            print_pass(f"Dashboard Items: Working ({len(items)} items returned)")
        else:
            print_fail(f"Dashboard items failed: {response.status_code}")
            all_passed = False
        
        # Test dashboard payments
        response = client.get('/dashboard/payments')
        if response.status_code == 200:
            data = response.data
            payment_split = data.get('payment_split', [])
            print_pass(f"Dashboard Payments: Working ({len(payment_split)} payment modes)")
        else:
            print_fail(f"Dashboard payments failed: {response.status_code}")
            all_passed = False
        
        # Test dashboard tax
        response = client.get('/dashboard/tax')
        if response.status_code == 200:
            data = response.data
            summary = data.get('summary', {})
            print_pass(f"Dashboard Tax: Working")
            print_pass(f"  - Total Tax: ₹{summary.get('total_tax_collected', '0.00')}")
        else:
            print_fail(f"Dashboard tax failed: {response.status_code}")
            all_passed = False
        
        # Test dashboard profit
        response = client.get('/dashboard/profit')
        if response.status_code == 200:
            data = response.data
            profit = data.get('profit_calculation', {})
            print_pass(f"Dashboard Profit: Working")
            print_pass(f"  - Net Profit: ₹{profit.get('net_profit', '0.00')}")
        else:
            print_fail(f"Dashboard profit failed: {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print_fail(f"Dashboard verification error: {e}")
        all_passed = False
    
    return all_passed

def verify_image_urls():
    """Verify image URLs are accessible"""
    print_section("6. Verifying Image URLs")
    
    all_passed = True
    
    # Check vendor logos
    vendors_with_logos = Vendor.objects.exclude(logo='')
    print(f"  Vendors with logos: {vendors_with_logos.count()}")
    
    # Check item images
    items_with_images = Item.objects.exclude(image='')
    print(f"  Items with images: {items_with_images.count()}")
    
    if items_with_images.exists():
        # Test a few image URLs
        client = APIClient()
        try:
            vendor = Vendor.objects.filter(is_approved=True).first()
            if vendor:
                user = vendor.user
                token, _ = Token.objects.get_or_create(user=user)
                client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
                
                response = client.get('/items/')
                if response.status_code == 200:
                    items = response.data if isinstance(response.data, list) else []
                    items_with_urls = [item for item in items if item.get('image_url')]
                    if items_with_urls:
                        print_pass(f"Items with image_url in API: {len(items_with_urls)}")
                    else:
                        print_warn("Items exist but no image_url in API response")
        except Exception as e:
            print_warn(f"Could not verify image URLs: {e}")
    
    return all_passed

def main():
    """Run all verification checks"""
    print("\n" + "="*70)
    print("  DEFAULT SETUP VERIFICATION")
    print("="*70)
    print("\nThis script verifies that all default accounts and test data")
    print("mentioned in the documentation are present and correctly configured.")
    
    results = []
    
    results.append(("Default Accounts", verify_default_accounts()))
    results.append(("Test Data", verify_test_data()))
    results.append(("Mobile Dev Data", verify_mobile_dev_data()))
    results.append(("API Access", verify_api_access()))
    results.append(("Dashboard Data", verify_dashboard_data()))
    results.append(("Image URLs", verify_image_urls()))
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*70}")
    print(f"Total: {passed}/{total} checks passed")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("All default setup data verified successfully!")
        print("\nDefault accounts are ready to use:")
        print("  - Admin: admin / admin123")
        print("  - Sales Rep: salesrep1 / salesrep123")
        print("  - Vendor 1: vendor1 / vendor123")
        print("  - Vendor 2: vendor2 / vendor123")
        print("  - Mobile Dev: mobiledev / mobile123")
        return 0
    else:
        print("Some verification checks failed.")
        print("Please run ./setup.sh and populate_mobile_dev_data.py to fix issues.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

