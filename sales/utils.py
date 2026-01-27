"""
Utility functions for sales/billing operations
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal


@transaction.atomic
def generate_bill_number(vendor):
    """
    Generate sequential bill number in format: {prefix}-{date}-{number}
    
    Format:
    - invoice_number: "INV-2026-01-27-0001" (full format with date)
    - bill_number: "INV-0001" (short format without date)
    
    Thread-safe using database-level locking via @transaction.atomic
    
    Args:
        vendor: Vendor instance
        
    Returns:
        tuple: (invoice_number, bill_number)
    """
    # Refresh vendor to get latest last_bill_number (prevents race conditions)
    vendor.refresh_from_db()
    
    # Get prefix (default to 'INV' if not set)
    prefix = (vendor.bill_prefix or 'INV').strip().upper()
    
    # Get date in YYYY-MM-DD format
    date_str = timezone.now().strftime('%Y-%m-%d')
    
    # Check if we need to initialize from starting_number
    if vendor.last_bill_number == 0 and vendor.bill_starting_number > 0:
        vendor.last_bill_number = vendor.bill_starting_number - 1
    
    # Increment bill number atomically
    vendor.last_bill_number += 1
    vendor.save(update_fields=['last_bill_number'])
    
    # Generate invoice_number and bill_number
    invoice_number = f"{prefix}-{date_str}-{vendor.last_bill_number:04d}"
    bill_number = f"{prefix}-{vendor.last_bill_number:04d}"
    
    return invoice_number, bill_number
