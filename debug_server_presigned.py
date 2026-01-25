#!/usr/bin/env python
"""Debug script to test pre-signed URL generation on server"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from items.models import Item
from auth_app.models import Vendor
from items.serializers import ItemSerializer
from rest_framework.test import APIRequestFactory
from backend.s3_utils import generate_presigned_url, get_s3_client
from django.conf import settings
import traceback

print("="*70)
print("SERVER PRE-SIGNED URL DEBUG")
print("="*70)
print()

# Check settings
print("1. SETTINGS CHECK:")
print(f"   USE_S3: {settings.USE_S3}")
print(f"   USE_S3_PRESIGNED_URLS: {getattr(settings, 'USE_S3_PRESIGNED_URLS', 'NOT SET')}")
print(f"   S3_PRESIGNED_URL_EXPIRATION: {getattr(settings, 'S3_PRESIGNED_URL_EXPIRATION', 'NOT SET')}")
print(f"   AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NOT SET')}")
print(f"   AWS_S3_REGION_NAME: {getattr(settings, 'AWS_S3_REGION_NAME', 'NOT SET')}")
print()

# Test S3 client
print("2. S3 CLIENT CHECK:")
try:
    s3_client = get_s3_client()
    if s3_client:
        print("   ✓ S3 client created")
    else:
        print("   ✗ S3 client is None")
        exit(1)
except Exception as e:
    print(f"   ✗ Error creating S3 client: {e}")
    traceback.print_exc()
    exit(1)
print()

# Get mobiledev vendor's item
print("3. TESTING WITH ACTUAL ITEM:")
vendor = Vendor.objects.filter(user__username='mobiledev').first()
if not vendor:
    print("   ✗ mobiledev vendor not found")
    exit(1)

item = Item.objects.filter(vendor=vendor, image__isnull=False).first()
if not item or not item.image:
    print("   ✗ No items with images found")
    exit(1)

print(f"   Item: {item.name}")
print(f"   Image name (S3 key): {item.image.name}")
print(f"   Image URL: {item.image.url}")
print()

# Test generate_presigned_url directly
print("4. TESTING generate_presigned_url FUNCTION:")
try:
    presigned = generate_presigned_url(item.image)
    if presigned:
        print(f"   ✓ Function returned URL")
        print(f"   Length: {len(presigned)} chars")
        print(f"   Has query params: {'?' in presigned}")
        if '?' in presigned and 'X-Amz' in presigned:
            print("   ✅ PRE-SIGNED URL GENERATED!")
            print(f"   URL preview: {presigned[:200]}...")
        else:
            print("   ⚠ URL returned but NOT pre-signed (no query params)")
            print(f"   URL: {presigned[:200]}...")
    else:
        print("   ✗ Function returned None")
        print("   This means pre-signed URL generation failed silently")
except Exception as e:
    print(f"   ✗ Error: {e}")
    traceback.print_exc()
print()

# Test serializer
print("5. TESTING SERIALIZER:")
try:
    factory = APIRequestFactory()
    request = factory.get('/items/')
    serializer = ItemSerializer(item, context={'request': request})
    image_url = serializer.data.get('image_url')
    
    if image_url:
        print(f"   ✓ Serializer returned image_url")
        print(f"   Has query params: {'?' in image_url}")
        if '?' in image_url and 'X-Amz' in image_url:
            print("   ✅ SERIALIZER RETURNS PRE-SIGNED URL!")
            print(f"   URL preview: {image_url[:200]}...")
        else:
            print("   ✗ SERIALIZER RETURNS DIRECT URL (NOT PRE-SIGNED)")
            print(f"   URL: {image_url[:200]}...")
            print()
            print("   DEBUGGING WHY:")
            # Check if function is being called
            presigned = generate_presigned_url(item.image)
            if presigned and '?' in presigned:
                print("   ⚠ Function works, but serializer not using it")
                print("   Check: settings.USE_S3_PRESIGNED_URLS might be False")
            elif presigned and '?' not in presigned:
                print("   ⚠ Function returned URL without query params")
            else:
                print("   ⚠ Function returned None - check logs for errors")
    else:
        print("   ✗ No image_url in serializer output")
except Exception as e:
    print(f"   ✗ Error: {e}")
    traceback.print_exc()
print()

print("="*70)
print("DIAGNOSIS COMPLETE")
print("="*70)

