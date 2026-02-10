#!/usr/bin/env python
"""
Comprehensive test script to verify all mobile developer setup
Tests all endpoints, data, images, and URLs
"""
import os
import sys
import django
import requests
from datetime import datetime
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.conf import settings
from items.models import Item, Category
from auth_app.models import Vendor
from sales.models import SalesBackup
from rest_framework.authtoken.models import Token

# Test configuration
BASE_URL = "http://localhost:8000"
USERNAME = "mobiledev"
PASSWORD = "mobile123"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def test_health_check():
    """Test health check endpoint"""
    print_header("1. HEALTH CHECK")
    try:
        # Try HTTP first
        try:
            response = requests.get(f"{BASE_URL}/health/", timeout=5)
            if response.status_code == 200:
                print_success(f"Health check (HTTP): {response.status_code}")
                data = response.json()
                print_info(f"Server: {data.get('server', 'unknown')}")
                print_info(f"Database: {data.get('database', 'unknown')}")
                return True
        except:
            # Fallback to Django test client
            client = Client()
            response = client.get('/health/')
            if response.status_code == 200:
                print_success(f"Health check (Test Client): {response.status_code}")
                data = response.json()
                print_info(f"Server: {data.get('server', 'unknown')}")
                print_info(f"Database: {data.get('database', 'unknown')}")
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_login():
    """Test login endpoint"""
    print_header("2. LOGIN ENDPOINT")
    try:
        # Try HTTP first
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"username": USERNAME, "password": PASSWORD},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                vendor = data.get('vendor', {})
                
                print_success(f"Login successful (HTTP): {response.status_code}")
                print_info(f"Token: {token[:20]}...")
                print_info(f"Username: {data.get('username')}")
                print_info(f"Business: {vendor.get('business_name')}")
                print_info(f"GST: {vendor.get('gst_no')}")
                print_info(f"FSSAI: {vendor.get('fssai_license')}")
                print_info(f"Logo URL: {vendor.get('logo_url', 'None')[:60]}...")
                print_info(f"Footer Note: {vendor.get('footer_note', 'None')[:50]}...")
                
                return token
        except:
            # Fallback to Django test client
            client = Client()
            response = client.post(
                '/auth/login',
                data={"username": USERNAME, "password": PASSWORD},
                content_type='application/json'
            )
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                vendor = data.get('vendor', {})
                
                print_success(f"Login successful (Test Client): {response.status_code}")
                print_info(f"Token: {token[:20]}...")
                print_info(f"Username: {data.get('username')}")
                print_info(f"Business: {vendor.get('business_name')}")
                print_info(f"GST: {vendor.get('gst_no')}")
                print_info(f"FSSAI: {vendor.get('fssai_license')}")
                print_info(f"Logo URL: {vendor.get('logo_url', 'None')[:60]}...")
                print_info(f"Footer Note: {vendor.get('footer_note', 'None')[:50]}...")
                
                return token
            else:
                print_error(f"Login failed: {response.status_code}")
                print_error(f"Response: {response.content.decode()[:200]}")
                return None
    except Exception as e:
        print_error(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_get_items(token):
    """Test get all items endpoint"""
    print_header("3. GET ALL ITEMS")
    try:
        # Try HTTP first
        try:
            response = requests.get(
                f"{BASE_URL}/items/",
                headers={"Authorization": f"Token {token}"},
                timeout=10
            )
        except:
            # Fallback to Django test client
            client = Client()
            response = client.get(
                '/items/',
                HTTP_AUTHORIZATION=f'Token {token}'
            )
        if response.status_code == 200:
            data = response.json()
            items = data.get('results', []) if isinstance(data, dict) else data
            
            print_success(f"Items fetched: {response.status_code}")
            print_info(f"Total items: {len(items)}")
            
            # Check items have required fields
            required_fields = ['id', 'name', 'mrp_price', 'price_type', 'hsn_code', 'hsn_gst_percentage', 'veg_nonveg', 'image_url']
            items_with_images = 0
            items_with_all_fields = 0
            
            for item in items[:5]:  # Check first 5
                has_image = bool(item.get('image_url'))
                if has_image:
                    items_with_images += 1
                    # Test image URL
                    img_url = item.get('image_url')
                    if img_url:
                        try:
                            # Check if pre-signed URL (has query params)
                            is_presigned = '?' in img_url and ('X-Amz-Algorithm' in img_url or 'X-Amz-Expires' in img_url)
                            if is_presigned:
                                # Pre-signed URL - use GET
                                img_response = requests.get(img_url, timeout=5, stream=True)
                                img_response.close()
                            else:
                                # Direct URL - use HEAD
                                img_response = requests.head(img_url, timeout=5)
                            
                            if img_response.status_code == 200:
                                print_success(f"  Image accessible: {item.get('name')}")
                            else:
                                print_warning(f"  Image not accessible: {item.get('name')} ({img_response.status_code})")
                        except Exception as img_err:
                            print_warning(f"  Could not verify image: {item.get('name')} ({str(img_err)[:30]})")
                
                has_all = all(item.get(field) is not None for field in required_fields)
                if has_all:
                    items_with_all_fields += 1
                else:
                    missing = [f for f in required_fields if item.get(f) is None]
                    print_warning(f"  {item.get('name')} missing: {', '.join(missing)}")
            
            print_info(f"Items with images: {items_with_images}/5 checked")
            print_info(f"Items with all fields: {items_with_all_fields}/5 checked")
            
            # Show sample item
            if items:
                sample = items[0]
                print_info(f"\nSample item structure:")
                print_info(f"  Name: {sample.get('name')}")
                print_info(f"  MRP: ₹{sample.get('mrp_price')}")
                print_info(f"  Price Type: {sample.get('price_type')}")
                print_info(f"  HSN: {sample.get('hsn_code', 'N/A')}, GST: {sample.get('hsn_gst_percentage', 0)}%")
                print_info(f"  Veg/Nonveg: {sample.get('veg_nonveg')}")
                img_url = sample.get('image_url', 'None')
                if img_url and img_url != 'None':
                    # Show if it's pre-signed (has query params)
                    is_presigned = '?' in img_url and ('X-Amz' in img_url or 'X-Amz-Algorithm' in img_url)
                    print_info(f"  Image: {img_url[:100]}...")
                    if is_presigned:
                        print_info(f"  ✓ Pre-signed URL detected")
                    else:
                        print_info(f"  ⚠ Direct URL (not pre-signed)")
                else:
                    print_info(f"  Image: None")
            
            return len(items)
        else:
            print_error(f"Get items failed: {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return 0
    except Exception as e:
        print_error(f"Get items error: {e}")
        return 0

def test_get_categories(token):
    """Test get all categories endpoint"""
    print_header("4. GET ALL CATEGORIES")
    try:
        # Try HTTP first
        try:
            response = requests.get(
                f"{BASE_URL}/items/categories/",
                headers={"Authorization": f"Token {token}"},
                timeout=10
            )
        except:
            # Fallback to Django test client
            client = Client()
            response = client.get(
                '/items/categories/',
                HTTP_AUTHORIZATION=f'Token {token}'
            )
        if response.status_code == 200:
            data = response.json()
            categories = data.get('results', []) if isinstance(data, dict) else data
            
            print_success(f"Categories fetched: {response.status_code}")
            print_info(f"Total categories: {len(categories)}")
            
            # Show categories
            for cat in categories:
                vendor_name = "Global" if not cat.get('vendor') else "Vendor-specific"
                print_info(f"  {cat.get('name')} ({vendor_name})")
            
            return len(categories)
        else:
            print_error(f"Get categories failed: {response.status_code}")
            return 0
    except Exception as e:
        print_error(f"Get categories error: {e}")
        return 0

def test_get_item_detail(token):
    """Test get item detail endpoint"""
    print_header("5. GET ITEM DETAIL")
    try:
        # First get items to get an ID
        try:
            response = requests.get(
                f"{BASE_URL}/items/",
                headers={"Authorization": f"Token {token}"},
                timeout=10
            )
        except:
            client = Client()
            response = client.get(
                '/items/',
                HTTP_AUTHORIZATION=f'Token {token}'
            )
        if response.status_code == 200:
            data = response.json()
            items = data.get('results', []) if isinstance(data, dict) else data
            if items:
                item_id = items[0].get('id')
                
                # Get item detail
                try:
                    detail_response = requests.get(
                        f"{BASE_URL}/items/{item_id}/",
                        headers={"Authorization": f"Token {token}"},
                        timeout=10
                    )
                except:
                    client = Client()
                    detail_response = client.get(
                        f'/items/{item_id}/',
                        HTTP_AUTHORIZATION=f'Token {token}'
                    )
                if detail_response.status_code == 200:
                    item = detail_response.json()
                    print_success(f"Item detail fetched: {detail_response.status_code}")
                    print_info(f"Item: {item.get('name')}")
                    print_info(f"Has image: {bool(item.get('image_url'))}")
                    print_info(f"Categories: {len(item.get('categories_list', []))}")
                    return True
                else:
                    print_error(f"Get item detail failed: {detail_response.status_code}")
                    return False
        return False
    except Exception as e:
        print_error(f"Get item detail error: {e}")
        return False

def test_create_bill(token):
    """Test create bill (sales backup) endpoint"""
    print_header("6. CREATE BILL (SALES BACKUP)")
    try:
        client = Client()
        
        # Get vendor info first
        try:
            login_response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"username": USERNAME, "password": PASSWORD},
                timeout=10
            )
            vendor_data = login_response.json().get('vendor', {})
        except:
            login_response = client.post(
                '/auth/login',
                data={"username": USERNAME, "password": PASSWORD},
                content_type='application/json'
            )
            vendor_data = login_response.json().get('vendor', {})
        
        # Get an item for the bill
        try:
            items_response = requests.get(
                f"{BASE_URL}/items/",
                headers={"Authorization": f"Token {token}"},
                timeout=10
            )
        except:
            items_response = client.get(
                '/items/',
                HTTP_AUTHORIZATION=f'Token {token}'
            )
        items = items_response.json().get('results', []) if isinstance(items_response.json(), dict) else items_response.json()
        
        if not items:
            print_warning("No items available for bill creation")
            return False
        
        item = items[0]
        
        # Create GST bill
        bill_data = {
            "device_id": "test-device-001",
            "bill_data": {
                "invoice_number": f"INV-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "bill_id": "test-bill-uuid-123",
                "billing_mode": "gst",
                "restaurant_name": vendor_data.get('business_name'),
                "address": "123 Developer Street, Tech City, State - 560001",
                "gstin": vendor_data.get('gst_no'),
                "fssai_license": vendor_data.get('fssai_license'),
                "bill_number": f"BN-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "bill_date": datetime.now().date().isoformat(),
                "items": [
                    {
                        "id": item.get('id'),
                        "name": item.get('name'),
                        "price": float(item.get('price', 0)),
                        "mrp_price": float(item.get('mrp_price', 0)),
                        "price_type": item.get('price_type'),
                        "hsn_code": item.get('hsn_code', ''),
                        "hsn_gst_percentage": float(item.get('hsn_gst_percentage', 0)),
                        "gst_percentage": float(item.get('hsn_gst_percentage', 0)), # Calculated from HSN
                        "quantity": 2,
                        "subtotal": float(item.get('mrp_price', 0)) * 2,
                        "item_gst": float(item.get('mrp_price', 0)) * 2 * float(item.get('hsn_gst_percentage', 0)) / 100 if item.get('price_type') == 'exclusive' else 0
                    }
                ],
                "subtotal": float(item.get('mrp_price', 0)) * 2,
                "cgst": float(item.get('mrp_price', 0)) * 2 * float(item.get('hsn_gst_percentage', 0)) / 200 if item.get('price_type') == 'exclusive' else 0,
                "sgst": float(item.get('mrp_price', 0)) * 2 * float(item.get('hsn_gst_percentage', 0)) / 200 if item.get('price_type') == 'exclusive' else 0,
                "igst": 0.00,
                "total_tax": float(item.get('mrp_price', 0)) * 2 * float(item.get('hsn_gst_percentage', 0)) / 100 if item.get('price_type') == 'exclusive' else 0,
                "total": float(item.get('mrp_price', 0)) * 2 + (float(item.get('mrp_price', 0)) * 2 * float(item.get('hsn_gst_percentage', 0)) / 100 if item.get('price_type') == 'exclusive' else 0),
                "footer_note": vendor_data.get('footer_note'),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/backup/sync",
                json=bill_data,
                headers={"Authorization": f"Token {token}"},
                timeout=10
            )
        except:
            response = client.post(
                '/backup/sync',
                data=bill_data,
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Token {token}'
            )
        
        if response.status_code in [200, 201]:
            print_success(f"Bill created: {response.status_code}")
            data = response.json()
            if 'bills' in data and len(data['bills']) > 0:
                bill = data['bills'][0]
                print_info(f"Bill ID: {bill.get('id')}")
                print_info(f"Bill Data: {bill.get('bill_data', {}).get('invoice_number')}")
            return True
        else:
            print_error(f"Create bill failed: {response.status_code}")
            print_error(f"Response: {response.text[:300]}")
            return False
    except Exception as e:
        print_error(f"Create bill error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_data():
    """Test database data directly"""
    print_header("7. DATABASE DATA VERIFICATION")
    try:
        vendor = Vendor.objects.get(user__username=USERNAME)
        items = Item.objects.filter(vendor=vendor, is_active=True)
        categories = Category.objects.filter(vendor=vendor) | Category.objects.filter(vendor=None)
        bills = SalesBackup.objects.filter(vendor=vendor)
        
        print_success("Database connection: OK")
        print_info(f"Vendor: {vendor.business_name}")
        print_info(f"Vendor logo: {'✅' if vendor.logo else '❌'}")
        print_info(f"Items: {items.count()}")
        print_info(f"Items with images: {items.exclude(image='').count()}")
        print_info(f"Categories: {categories.count()}")
        print_info(f"Bills: {bills.count()}")
        
        # Check item fields
        sample_item = items.first()
        if sample_item:
            print_info(f"\nSample item fields:")
            print_info(f"  mrp_price: {'✅' if sample_item.mrp_price else '❌'}")
            print_info(f"  price_type: {'✅' if sample_item.price_type else '❌'}")
            print_info(f"  hsn_code: {'✅' if sample_item.hsn_code else '❌'}")
            print_info(f"  hsn_gst_percentage: {'✅' if sample_item.hsn_gst_percentage is not None else '❌'}")
            print_info(f"  veg_nonveg: {'✅' if sample_item.veg_nonveg else '❌'}")
            print_info(f"  image: {'✅' if sample_item.image else '❌'}")
        
        return True
    except Exception as e:
        print_error(f"Database verification error: {e}")
        return False

def test_image_urls(token):
    """Test all image URLs are accessible"""
    print_header("8. IMAGE URL VERIFICATION")
    try:
        try:
            response = requests.get(
                f"{BASE_URL}/items/",
                headers={"Authorization": f"Token {token}"},
                timeout=10
            )
        except:
            client = Client()
            response = client.get(
                '/items/',
                HTTP_AUTHORIZATION=f'Token {token}'
            )
        if response.status_code == 200:
            data = response.json()
            items = data.get('results', []) if isinstance(data, dict) else data
            
            accessible = 0
            not_accessible = 0
            
            for item in items:
                img_url = item.get('image_url')
                if img_url:
                    try:
                        # Use GET instead of HEAD - pre-signed URLs work better with GET
                        # Also check if URL is pre-signed (has query params)
                        is_presigned = '?' in img_url and ('X-Amz-Algorithm' in img_url or 'X-Amz-Expires' in img_url)
                        if is_presigned:
                            # Pre-signed URL - use GET request
                            img_response = requests.get(img_url, timeout=10, allow_redirects=True, stream=True)
                            # For GET, we just need to check status, don't download full image
                            img_response.close()
                        else:
                            # Direct URL - try HEAD first, fallback to GET
                            try:
                                img_response = requests.head(img_url, timeout=10, allow_redirects=True)
                            except:
                                img_response = requests.get(img_url, timeout=10, allow_redirects=True, stream=True)
                                img_response.close()
                        
                        if img_response.status_code == 200:
                            accessible += 1
                        else:
                            not_accessible += 1
                            print_warning(f"  {item.get('name')}: {img_response.status_code}")
                    except Exception as e:
                        not_accessible += 1
                        print_warning(f"  {item.get('name')}: Error - {str(e)[:50]}")
                else:
                    not_accessible += 1
                    print_warning(f"  {item.get('name')}: No image URL")
            
            print_info(f"Accessible images: {accessible}/{len(items)}")
            print_info(f"Not accessible: {not_accessible}/{len(items)}")
            
            return accessible == len(items)
        return False
    except Exception as e:
        print_error(f"Image URL verification error: {e}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}COMPREHENSIVE MOBILE DEVELOPER SETUP TEST{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Username: {USERNAME}")
    print_info(f"Testing all endpoints, data, and URLs...\n")
    
    results = {}
    
    # Run tests
    results['health'] = test_health_check()
    token = test_login()
    results['login'] = token is not None
    
    if not token:
        print_error("\n❌ Login failed! Cannot continue tests.")
        return
    
    results['items'] = test_get_items(token) > 0
    results['categories'] = test_get_categories(token) > 0
    results['item_detail'] = test_get_item_detail(token)
    results['create_bill'] = test_create_bill(token)
    results['database'] = test_database_data()
    results['images'] = test_image_urls(token)
    
    # Summary
    print_header("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name.upper()}: PASSED")
        else:
            print_error(f"{test_name.upper()}: FAILED")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}\n")
    
    if passed == total:
        print_success("✅ ALL TESTS PASSED! Mobile developer setup is ready!")
    else:
        print_error("❌ SOME TESTS FAILED! Please check the errors above.")
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}\n")

if __name__ == '__main__':
    main()

