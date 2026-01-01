#!/usr/bin/env python
"""
Script to ensure all default users are created and working
Run this after setup to verify all default users exist
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from auth_app.models import Vendor, SalesRep
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

def ensure_user(username, email, password, is_staff=False, is_superuser=False):
    """Ensure a user exists with correct password"""
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_active': True,
            'is_staff': is_staff,
            'is_superuser': is_superuser
        }
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f'✓ Created user: {username}')
    else:
        # Update existing user
        user.email = email
        user.is_active = True
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.set_password(password)  # Reset password to ensure it's correct
        user.save()
        print(f'✓ Updated user: {username}')
    
    # Ensure token exists
    Token.objects.get_or_create(user=user)
    
    # Verify password
    if user.check_password(password):
        print(f'  ✓ Password verified')
    else:
        print(f'  ✗ Password verification failed!')
        return False
    
    # Verify authentication
    auth_user = authenticate(username=username, password=password)
    if auth_user:
        print(f'  ✓ Authentication works')
    else:
        print(f'  ✗ Authentication failed!')
        return False
    
    return True

def ensure_sales_rep(username, name):
    """Ensure sales rep profile exists"""
    try:
        user = User.objects.get(username=username)
        sales_rep, created = SalesRep.objects.get_or_create(
            user=user,
            defaults={
                'name': name,
                'is_active': True
            }
        )
        
        if created:
            print(f'✓ Created sales rep profile for {username}')
        else:
            sales_rep.name = name
            sales_rep.is_active = True
            print(f'✓ Updated sales rep profile for {username}')
        
        # Verify
        if hasattr(user, 'sales_rep_profile') and user.sales_rep_profile.is_active:
            print(f'  ✓ Sales rep profile active')
            return True
        else:
            print(f'  ✗ Sales rep profile not active!')
            return False
    except User.DoesNotExist:
        print(f'✗ User {username} does not exist!')
        return False

def main():
    print("=" * 60)
    print("Ensuring Default Users Are Created and Working")
    print("=" * 60)
    print()
    
    success = True
    
    # Admin user
    print("1. Admin User:")
    if not ensure_user('admin', 'admin@pos.local', 'admin123', is_staff=True, is_superuser=True):
        success = False
    print()
    
    # Test user
    print("2. Test User:")
    if not ensure_user('testuser', 'test@pos.local', 'test123'):
        success = False
    print()
    
    # Sales rep user
    print("3. Sales Rep User:")
    if not ensure_user('salesrep1', 'salesrep1@pos.local', 'salesrep123'):
        success = False
    if not ensure_sales_rep('salesrep1', 'Sales Rep 1'):
        success = False
    print()
    
    print("=" * 60)
    if success:
        print("✓ All default users are created and working!")
        print()
        print("Login Credentials:")
        print("  Admin:     admin / admin123")
        print("  Test User: testuser / test123")
        print("  Sales Rep: salesrep1 / salesrep123")
        print()
        print("URLs:")
        print("  Admin:     http://localhost:8000/admin/")
        print("  Sales Rep: http://localhost:8000/sales-rep/")
        return 0
    else:
        print("✗ Some users failed to create/verify!")
        return 1

if __name__ == '__main__':
    sys.exit(main())

