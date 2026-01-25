#!/usr/bin/env python
"""
Populate comprehensive test data for mobile app development
Creates approved vendors, categories, items with GST fields, and sample bills
"""
import os
import sys
import django
import uuid
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from PIL import Image
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile
from auth_app.models import Vendor
from items.models import Category, Item
from sales.models import Bill, BillItem, SalesBackup
from rest_framework.authtoken.models import Token

def download_vendor_logo():
    """Download a restaurant logo image"""
    try:
        # Use a restaurant/food related image from Unsplash (direct URL)
        url = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=200&fit=crop"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        
        if response.status_code == 200 and response.content and len(response.content) > 1000:
            img = Image.open(BytesIO(response.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to 400x200
            img = img.resize((400, 200), Image.Resampling.LANCZOS)
            
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=85)
            img_io.seek(0)
            
            logo_file = InMemoryUploadedFile(
                img_io, None, "logo.jpg",
                'image/jpeg', img_io.tell(), None
            )
            
            return logo_file
    except Exception as e:
        pass
    
    return None

def create_mobile_dev_vendor():
    """Create a fully configured vendor for mobile development"""
    print("\n📦 Creating mobile dev vendor...")
    
    # Main vendor for mobile development
    vendor_user, created = User.objects.get_or_create(
        username='mobiledev',
        defaults={
            'email': 'mobiledev@pos.local',
            'first_name': 'Mobile',
            'last_name': 'Developer',
            'is_active': True,
        }
    )
    if created:
        vendor_user.set_password('mobile123')
        vendor_user.save()
        print("  ✓ Created mobiledev user")
    else:
        vendor_user.set_password('mobile123')
        vendor_user.is_active = True
        vendor_user.save()
        print("  ✓ Updated mobiledev user")
    
    business_name = 'Mobile Dev Restaurant'
    
    # Download vendor logo
    print("  📥 Downloading vendor logo...")
    try:
        logo_file = download_vendor_logo()
        if logo_file:
            print("  ✓ Vendor logo downloaded")
        else:
            print("  ⚠️ Could not download vendor logo")
    except Exception as e:
        print(f"  ⚠️ Error downloading vendor logo: {e}")
        logo_file = None
    
    vendor, created = Vendor.objects.get_or_create(
        user=vendor_user,
        defaults={
            'business_name': business_name,
            'phone': '+919876543210',
            'gst_no': '29MOBILE1234D1E5',
            'fssai_license': '12345678901234',
            'address': '123 Developer Street, Tech City, State - 560001',
            'footer_note': 'Thank you for visiting! We appreciate your business.',
            'logo': logo_file,
            'is_approved': True,
        }
    )
    if not created:
        vendor.is_approved = True
        vendor.business_name = business_name
        vendor.gst_no = '29MOBILE1234D1E5'
        vendor.fssai_license = '12345678901234'
        vendor.footer_note = 'Thank you for visiting! We appreciate your business.'
        # Add logo if it doesn't exist
        if not vendor.logo and logo_file:
            vendor.logo = logo_file
        vendor.save()
    
    vendor_user.is_active = True
    vendor_user.save()
    token, _ = Token.objects.get_or_create(user=vendor_user)
    
    logo_status = "📷" if vendor.logo else "📷❌"
    print(f"  ✓ Vendor: mobiledev / mobile123 (APPROVED) {logo_status}")
    print(f"  ✓ Token: {token.key}")
    print(f"  ✓ Business: {vendor.business_name}")
    print(f"  ✓ GST: {vendor.gst_no}")
    print(f"  ✓ FSSAI: {vendor.fssai_license}")
    
    return vendor

def create_comprehensive_categories(vendor):
    """Create all required categories for mobile development"""
    print("\n📁 Creating comprehensive categories...")
    
    # Global categories (available to all vendors)
    global_categories = [
        {'name': 'Beverage', 'description': 'Drinks and beverages', 'sort_order': 1},
        {'name': 'Snacks', 'description': 'Snacks and quick bites', 'sort_order': 2},
    ]
    
    for cat_data in global_categories:
        cat, created = Category.objects.get_or_create(
            name=cat_data['name'],
            vendor=None,
            defaults=cat_data
        )
        if created:
            print(f"  ✓ Created global category: {cat_data['name']}")
        else:
            print(f"  ✓ Global category exists: {cat_data['name']}")
    
    # Vendor-specific categories (as per requirements)
    vendor_categories = [
        {'name': 'Breakfast', 'description': 'Breakfast items', 'sort_order': 1, 'vendor': vendor},
        {'name': 'Lunch', 'description': 'Lunch items', 'sort_order': 2, 'vendor': vendor},
        {'name': 'Dinner', 'description': 'Dinner items', 'sort_order': 3, 'vendor': vendor},
        {'name': 'Snacks', 'description': 'Snacks and appetizers', 'sort_order': 4, 'vendor': vendor},
        {'name': 'Beverage', 'description': 'Beverages and drinks', 'sort_order': 5, 'vendor': vendor},
        {'name': 'Desserts', 'description': 'Sweet treats and desserts', 'sort_order': 6, 'vendor': vendor},
    ]
    
    vendor_cats = []
    for cat_data in vendor_categories:
        vendor_obj = cat_data.pop('vendor')
        cat, created = Category.objects.get_or_create(
            name=cat_data['name'],
            vendor=vendor_obj,
            defaults=cat_data
        )
        vendor_cats.append(cat)
        if created:
            print(f"  ✓ Created category: {cat_data['name']}")
        else:
            print(f"  ✓ Category exists: {cat_data['name']}")
    
    return vendor_cats

def download_food_image(item_name, item_type='veg'):
    """Download real food image from reliable image sources"""
    # Map item names to working image URLs from Pexels, Unsplash, etc.
    # Using direct image URLs that are known to work
    food_image_urls = {
        'Masala Dosa': 'https://images.pexels.com/photos/5560763/pexels-photo-5560763.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Idli Sambar': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Egg Omelette': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Biryani': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Veg Thali': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Chicken Curry': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Butter Naan': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Paneer Tikka': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Samosa': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Chicken Wings': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
        'Coca Cola': 'https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400&h=400&fit=crop',
        'Fresh Lime Soda': 'https://images.unsplash.com/photo-1523677011783-c91d1bbe2fdc?w=400&h=400&fit=crop',
        'Coffee': 'https://images.unsplash.com/photo-1517487881594-2787fef5ebf7?w=400&h=400&fit=crop',
        'Ice Cream': 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400&h=400&fit=crop',
        'Gulab Jamun': 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop',
    }
    
    # Get URL for this item
    url = food_image_urls.get(item_name)
    
    # If no specific URL, use Picsum (random but reliable)
    if not url:
        url = f'https://picsum.photos/400/400?random={hash(item_name) % 1000}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Try primary URL
    try:
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        
        if response.status_code == 200 and response.content and len(response.content) > 5000:
            # Verify it's an image
            try:
                img = Image.open(BytesIO(response.content))
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to 400x400
                img = img.resize((400, 400), Image.Resampling.LANCZOS)
                
                # Save to BytesIO
                img_io = BytesIO()
                img.save(img_io, format='JPEG', quality=85)
                img_io.seek(0)
                
                # Create Django file
                image_file = InMemoryUploadedFile(
                    img_io, None, f"{item_name.replace(' ', '_').lower()}.jpg",
                    'image/jpeg', img_io.tell(), None
                )
                
                return image_file
            except Exception as img_error:
                # Not a valid image
                pass
    except Exception as e:
        pass
    
    # Fallback: Use Picsum (always works)
    try:
        fallback_url = f'https://picsum.photos/400/400?random={hash(item_name) % 1000}'
        response = requests.get(fallback_url, timeout=15, headers=headers, allow_redirects=True)
        
        if response.status_code == 200 and response.content and len(response.content) > 5000:
            img = Image.open(BytesIO(response.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img = img.resize((400, 400), Image.Resampling.LANCZOS)
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=85)
            img_io.seek(0)
            image_file = InMemoryUploadedFile(
                img_io, None, f"{item_name.replace(' ', '_').lower()}.jpg",
                'image/jpeg', img_io.tell(), None
            )
            return image_file
    except:
        pass
    
    return None

def create_comprehensive_items(vendor, categories):
    """Create comprehensive items with all GST and pricing fields"""
    print("\n🛍️ Creating comprehensive items with GST fields...")
    
    # Get category references
    breakfast_cat = next((c for c in categories if c.name == 'Breakfast'), None)
    lunch_cat = next((c for c in categories if c.name == 'Lunch'), None)
    dinner_cat = next((c for c in categories if c.name == 'Dinner'), None)
    snacks_cat = next((c for c in categories if c.name == 'Snacks'), None)
    beverage_cat = next((c for c in categories if c.name == 'Beverage'), None)
    desserts_cat = next((c for c in categories if c.name == 'Desserts'), None)
    
    # Comprehensive items with all new fields
    items_data = [
        # Breakfast Items
        {
            'name': 'Masala Dosa',
            'description': 'Crispy dosa with spicy potato filling',
            'price': Decimal('60.00'),
            'mrp_price': Decimal('70.00'),
            'price_type': 'exclusive',
            'gst_percentage': Decimal('5.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 50,
            'sku': 'DOSA-001',
            'is_active': True,
            'sort_order': 1,
            'categories': [breakfast_cat] if breakfast_cat else [],
        },
        {
            'name': 'Idli Sambar',
            'description': 'Soft idlis with sambar and chutney',
            'price': Decimal('40.00'),
            'mrp_price': Decimal('45.00'),
            'price_type': 'inclusive',
            'gst_percentage': Decimal('5.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 60,
            'sku': 'IDLI-001',
            'is_active': True,
            'sort_order': 2,
            'categories': [breakfast_cat] if breakfast_cat else [],
        },
        {
            'name': 'Egg Omelette',
            'description': 'Fresh egg omelette with bread',
            'price': Decimal('50.00'),
            'mrp_price': Decimal('55.00'),
            'price_type': 'exclusive',
            'gst_percentage': Decimal('5.00'),
            'veg_nonveg': 'nonveg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 40,
            'sku': 'EGG-001',
            'is_active': True,
            'sort_order': 3,
            'categories': [breakfast_cat] if breakfast_cat else [],
        },
        
        # Lunch Items
        {
            'name': 'Biryani',
            'description': 'Fragrant basmati rice with spices',
            'price': Decimal('150.00'),
            'mrp_price': Decimal('180.00'),
            'price_type': 'exclusive',
            'gst_percentage': Decimal('18.00'),
            'veg_nonveg': 'nonveg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 30,
            'sku': 'BIRY-001',
            'is_active': True,
            'sort_order': 4,
            'categories': [lunch_cat] if lunch_cat else [],
        },
        {
            'name': 'Veg Thali',
            'description': 'Complete vegetarian meal',
            'price': Decimal('120.00'),
            'mrp_price': Decimal('140.00'),
            'price_type': 'exclusive',
            'gst_percentage': Decimal('18.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('10.00'),
            'stock_quantity': 25,
            'sku': 'THALI-001',
            'is_active': True,
            'sort_order': 5,
            'categories': [lunch_cat] if lunch_cat else [],
        },
        {
            'name': 'Chicken Curry',
            'description': 'Spicy chicken curry with rice',
            'price': Decimal('180.00'),
            'mrp_price': Decimal('200.00'),
            'price_type': 'exclusive',
            'gst_percentage': Decimal('18.00'),
            'veg_nonveg': 'nonveg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 20,
            'sku': 'CHICK-001',
            'is_active': True,
            'sort_order': 6,
            'categories': [lunch_cat, dinner_cat] if lunch_cat and dinner_cat else [],
        },
        
        # Dinner Items
        {
            'name': 'Butter Naan',
            'description': 'Fresh butter naan',
            'price': Decimal('30.00'),
            'mrp_price': Decimal('35.00'),
            'price_type': 'inclusive',
            'gst_percentage': Decimal('5.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 100,
            'sku': 'NAAN-001',
            'is_active': True,
            'sort_order': 7,
            'categories': [dinner_cat] if dinner_cat else [],
        },
        {
            'name': 'Paneer Tikka',
            'description': 'Grilled paneer with spices',
            'price': Decimal('140.00'),
            'mrp_price': Decimal('160.00'),
            'price_type': 'exclusive',
            'gst_percentage': Decimal('18.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 35,
            'sku': 'PANEER-001',
            'is_active': True,
            'sort_order': 8,
            'categories': [dinner_cat] if dinner_cat else [],
        },
        
        # Snacks
        {
            'name': 'Samosa',
            'description': 'Crispy samosa with chutney',
            'price': Decimal('20.00'),
            'mrp_price': Decimal('25.00'),
            'price_type': 'inclusive',
            'gst_percentage': Decimal('5.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 80,
            'sku': 'SAM-001',
            'is_active': True,
            'sort_order': 9,
            'categories': [snacks_cat] if snacks_cat else [],
        },
        {
            'name': 'Chicken Wings',
            'description': 'Spicy chicken wings',
            'price': Decimal('120.00'),
            'mrp_price': Decimal('140.00'),
            'price_type': 'exclusive',
            'gst_percentage': Decimal('18.00'),
            'veg_nonveg': 'nonveg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 30,
            'sku': 'WINGS-001',
            'is_active': True,
            'sort_order': 10,
            'categories': [snacks_cat] if snacks_cat else [],
        },
        
        # Beverages
        {
            'name': 'Coca Cola',
            'description': 'Cold carbonated drink',
            'price': Decimal('25.00'),
            'mrp_price': Decimal('30.00'),
            'price_type': 'inclusive',
            'gst_percentage': Decimal('18.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 150,
            'sku': 'COKE-001',
            'is_active': True,
            'sort_order': 11,
            'categories': [beverage_cat] if beverage_cat else [],
        },
        {
            'name': 'Fresh Lime Soda',
            'description': 'Refreshing lime soda',
            'price': Decimal('40.00'),
            'mrp_price': Decimal('45.00'),
            'price_type': 'inclusive',
            'gst_percentage': Decimal('5.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 100,
            'sku': 'LIME-001',
            'is_active': True,
            'sort_order': 12,
            'categories': [beverage_cat] if beverage_cat else [],
        },
        {
            'name': 'Coffee',
            'description': 'Hot coffee',
            'price': Decimal('30.00'),
            'mrp_price': Decimal('35.00'),
            'price_type': 'inclusive',
            'gst_percentage': Decimal('5.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 120,
            'sku': 'COFFEE-001',
            'is_active': True,
            'sort_order': 13,
            'categories': [beverage_cat] if beverage_cat else [],
        },
        
        # Desserts
        {
            'name': 'Ice Cream',
            'description': 'Vanilla ice cream',
            'price': Decimal('60.00'),
            'mrp_price': Decimal('70.00'),
            'price_type': 'exclusive',
            'gst_percentage': Decimal('18.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 50,
            'sku': 'ICE-001',
            'is_active': True,
            'sort_order': 14,
            'categories': [desserts_cat] if desserts_cat else [],
        },
        {
            'name': 'Gulab Jamun',
            'description': 'Sweet gulab jamun',
            'price': Decimal('50.00'),
            'mrp_price': Decimal('60.00'),
            'price_type': 'inclusive',
            'gst_percentage': Decimal('5.00'),
            'veg_nonveg': 'veg',
            'additional_discount': Decimal('0.00'),
            'stock_quantity': 40,
            'sku': 'GULAB-001',
            'is_active': True,
            'sort_order': 15,
            'categories': [desserts_cat] if desserts_cat else [],
        },
    ]
    
    created_count = 0
    print("  📥 Downloading images from internet...")
    for idx, item_data in enumerate(items_data, 1):
        categories_list = item_data.pop('categories', [])
        veg_nonveg = item_data.get('veg_nonveg', 'veg')
        item_name = item_data['name']
        
        # Download real image from internet
        print(f"    [{idx}/{len(items_data)}] Downloading image for {item_name}...", end=' ', flush=True)
        try:
            image_file = download_food_image(item_name, veg_nonveg)
            if image_file:
                item_data['image'] = image_file
                print("✓")
            else:
                item_data['image'] = None
                print("✗ (skipped)")
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        except Exception as e:
            print(f"✗ ({str(e)[:30]})")
            item_data['image'] = None
        
        item, created = Item.objects.get_or_create(
            name=item_data['name'],
            vendor=vendor,
            defaults=item_data
        )
        
        # If item already exists, update image if it doesn't have one OR if image file doesn't exist in S3
        should_update_image = not created and not item.image
        if not should_update_image and item.image:
            # Check if image file actually exists in S3
            try:
                from backend.s3_utils import get_s3_client
                from django.conf import settings
                s3_client = get_s3_client()
                if s3_client:
                    s3_client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=item.image.name)
            except:
                # File doesn't exist in S3, force update
                should_update_image = True
        
        if should_update_image:
            try:
                image_file = create_item_image(item_data['name'], veg_nonveg)
                item.image = image_file
                item.save()
            except Exception as e:
                print(f"  ⚠️ Could not add image to existing {item_data['name']}: {e}")
        
        if categories_list:
            item.categories.set(categories_list)
        if created:
            created_count += 1
            image_status = "📷" if item.image else "📷❌"
            print(f"  ✓ Created: {item_data['name']} (₹{item_data['mrp_price']}, {item_data['gst_percentage']}% GST, {item_data['veg_nonveg']}) {image_status}")
        else:
            # Update existing item with new fields if missing
            if not item.mrp_price:
                item.mrp_price = item_data['mrp_price']
            if not item.price_type:
                item.price_type = item_data['price_type']
            if not item.gst_percentage:
                item.gst_percentage = item_data['gst_percentage']
            if not item.veg_nonveg:
                item.veg_nonveg = item_data['veg_nonveg']
            item.save()
            image_status = "📷" if item.image else "📷❌"
            print(f"  ✓ Updated: {item_data['name']} {image_status}")
    
    total_items = len(items_data)
    print(f"\n  ✅ Created/Updated {total_items} items")
    # Return total items processed (not just newly created)
    return total_items

def create_sample_bills(vendor):
    """Create sample bills using new Bill and BillItem models (GST and Non-GST)"""
    print("\n🧾 Creating sample bills...")
    
    # Get some items for bills
    items = Item.objects.filter(vendor=vendor, is_active=True)[:5]
    if not items:
        print("  ⚠️ No items found. Skipping bill creation.")
        return
    
    # Check for existing bills and generate unique invoice numbers
    bill_date = timezone.now().date()
    created_at = timezone.now()
    year = bill_date.year
    
    # Find the highest invoice number for this vendor in this year
    existing_bills = Bill.objects.filter(
        vendor=vendor,
        invoice_number__startswith=f'INV-{year}-'
    ).order_by('-invoice_number')
    
    if existing_bills.exists():
        # Extract the highest number
        last_bill = existing_bills.first()
        try:
            last_num = int(last_bill.invoice_number.split('-')[-1])
            next_num = last_num + 1
        except:
            next_num = 1
    else:
        next_num = 1
    
    # Generate invoice numbers
    gst_invoice_number = f'INV-{year}-{next_num:03d}'
    non_gst_invoice_number = f'INV-{year}-{next_num + 1:03d}'
    
    # Check if these invoice numbers already exist (shouldn't, but be safe)
    if Bill.objects.filter(vendor=vendor, invoice_number=gst_invoice_number).exists():
        print(f"  ⚠️ Bill {gst_invoice_number} already exists. Skipping GST bill creation.")
        return
    if Bill.objects.filter(vendor=vendor, invoice_number=non_gst_invoice_number).exists():
        print(f"  ⚠️ Bill {non_gst_invoice_number} already exists. Skipping Non-GST bill creation.")
        return
    
    # Calculate GST bill totals
    gst_items = items[:3]
    subtotal = sum(float(item.mrp_price * 2) for item in gst_items)
    total_tax = sum(float((item.mrp_price * 2 * item.gst_percentage) / 100) for item in gst_items if item.price_type == 'exclusive')
    cgst = total_tax / 2  # Split equally for intra-state
    sgst = total_tax / 2
    total = subtotal + total_tax
    
    gst_bill = Bill.objects.create(
        vendor=vendor,
        device_id='mobile-dev-device-001',
        invoice_number=gst_invoice_number,
        bill_number=f'BN-{year}-{next_num:03d}',
        bill_date=bill_date,
        restaurant_name=vendor.business_name,
        address=vendor.address,
        gstin=vendor.gst_no,
        fssai_license=vendor.fssai_license,
        footer_note=vendor.footer_note,
        billing_mode='gst',
        subtotal=Decimal(str(subtotal)),
        total_amount=Decimal(str(total)),
        total_tax=Decimal(str(total_tax)),
        cgst_amount=Decimal(str(cgst)),
        sgst_amount=Decimal(str(sgst)),
        igst_amount=Decimal('0.00'),
        payment_mode='cash',
        created_at=created_at
    )
    
    # Create bill items
    for item in gst_items:
        quantity = Decimal('2.00')
        item_subtotal = item.mrp_price * quantity
        item_gst = (item_subtotal * item.gst_percentage / 100) if item.price_type == 'exclusive' else Decimal('0.00')
        
        BillItem.objects.create(
            bill=gst_bill,
            item=item,
            original_item_id=item.id,
            item_name=item.name,
            item_description=item.description,
            price=item.price or item.mrp_price,
            mrp_price=item.mrp_price,
            price_type=item.price_type,
            quantity=quantity,
            subtotal=item_subtotal,
            gst_percentage=item.gst_percentage,
            item_gst_amount=item_gst,
            veg_nonveg=item.veg_nonveg,
            additional_discount=item.additional_discount,
        )
    
    print(f"  ✓ Created GST Bill: {gst_bill.invoice_number} (₹{gst_bill.total_amount:.2f})")
    
    # Sample Non-GST Bill
    non_gst_items = items[3:5]
    non_gst_subtotal = sum(float(item.mrp_price) for item in non_gst_items)
    non_gst_total = non_gst_subtotal
    
    non_gst_bill = Bill.objects.create(
        vendor=vendor,
        device_id='mobile-dev-device-001',
        invoice_number=non_gst_invoice_number,
        bill_number=f'BN-{year}-{next_num + 1:03d}',
        bill_date=bill_date,
        restaurant_name=vendor.business_name,
        address=vendor.address,
        gstin=vendor.gst_no,
        fssai_license=vendor.fssai_license,
        footer_note=vendor.footer_note,
        billing_mode='non_gst',
        subtotal=Decimal(str(non_gst_subtotal)),
        total_amount=Decimal(str(non_gst_total)),
        total_tax=Decimal('0.00'),
        cgst_amount=Decimal('0.00'),
        sgst_amount=Decimal('0.00'),
        igst_amount=Decimal('0.00'),
        payment_mode='cash',
        created_at=created_at
    )
    
    # Create bill items for non-GST bill
    for item in non_gst_items:
        quantity = Decimal('1.00')
        item_subtotal = item.mrp_price * quantity
        
        BillItem.objects.create(
            bill=non_gst_bill,
            item=item,
            original_item_id=item.id,
            item_name=item.name,
            item_description=item.description,
            price=item.price or item.mrp_price,
            mrp_price=item.mrp_price,
            price_type=item.price_type,
            quantity=quantity,
            subtotal=item_subtotal,
            gst_percentage=Decimal('0.00'),  # No GST for non-GST bills
            item_gst_amount=Decimal('0.00'),
            veg_nonveg=item.veg_nonveg,
            additional_discount=item.additional_discount,
        )
    
    print(f"  ✓ Created Non-GST Bill: {non_gst_bill.invoice_number} (₹{non_gst_bill.total_amount:.2f})")
    
    print(f"\n  ✅ Created 2 sample bills (1 GST, 1 Non-GST)")

def main():
    """Main function to populate all data"""
    print("\n" + "="*70)
    print("  POPULATING MOBILE APP DEVELOPMENT DATA")
    print("="*70)
    
    try:
        # Create vendor
        vendor = create_mobile_dev_vendor()
        
        # Create categories
        categories = create_comprehensive_categories(vendor)
        
        # Create items
        items_count = create_comprehensive_items(vendor, categories)
        
        # Create sample bills
        create_sample_bills(vendor)
        
        # Get token for API access
        token = Token.objects.get(user=vendor.user)
        
        print("\n" + "="*70)
        print("  ✅ DATA POPULATION COMPLETE")
        print("="*70)
        print("\n📋 Mobile Developer Account:")
        print(f"   Username: mobiledev")
        print(f"   Password: mobile123")
        print(f"   Token: {token.key}")
        print(f"   Business: {vendor.business_name}")
        print(f"   GST: {vendor.gst_no}")
        print(f"   FSSAI: {vendor.fssai_license}")
        print(f"\n📦 Data Created:")
        print(f"   • Categories: {len(categories)} vendor-specific + 2 global")
        print(f"   • Items: {items_count} items with full GST fields")
        print(f"   • Bills: 2 sample bills (GST + Non-GST)")
        print(f"\n🔗 API Endpoints:")
        print(f"   • Login: POST /auth/login")
        print(f"   • Items: GET /items/")
        print(f"   • Categories: GET /items/categories/")
        print(f"   • Sales Backup: POST /backup/sync")
        print("\n" + "="*70 + "\n")
        
        return 0
    except Exception as e:
        print(f"\n❌ Error populating data: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

