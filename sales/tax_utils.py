"""
Tax calculation utilities for HSN and SAC codes
"""
import json
import os
from decimal import Decimal
from django.conf import settings

# Load HSN to GST mapping (for reference/validation only)
HSN_MAPPING = None
SAC_MAPPING = None

def load_hn_mapping():
    """Load HSN to GST mapping from JSON file (for reference only)"""
    global HSN_MAPPING
    if HSN_MAPPING is None:
        file_path = os.path.join(os.path.dirname(__file__), 'hsn_to_gst_mapping.json')
        try:
            with open(file_path, 'r') as f:
                HSN_MAPPING = json.load(f)
        except FileNotFoundError:
            HSN_MAPPING = {}
    return HSN_MAPPING

def load_sac_mapping():
    """Load SAC to GST mapping from JSON file (for reference only)"""
    global SAC_MAPPING
    if SAC_MAPPING is None:
        file_path = os.path.join(os.path.dirname(__file__), 'sac_to_gst_mapping.json')
        try:
            with open(file_path, 'r') as f:
                SAC_MAPPING = json.load(f)
        except FileNotFoundError:
            SAC_MAPPING = {}
    return SAC_MAPPING

def get_default_gst_from_hn(hn_code):
    """
    Get default GST percentage from HSN code mapping (for reference/validation)
    
    Args:
        hsn_code: HSN code as string (e.g., "2106", "2202")
    
    Returns:
        Decimal: Default GST percentage from mapping, or 0 if not found
    """
    if not hsn_code:
        return Decimal('0')
    
    mapping = load_hn_mapping()
    hsn_str = str(hsn_code).strip()
    
    if hsn_str in mapping:
        return Decimal(str(mapping[hsn_str]['gst_percentage']))
    
    return Decimal('0')

def get_default_gst_from_sac(sac_code):
    """
    Get default GST percentage from SAC code mapping (for reference/validation)
    
    Args:
        sac_code: SAC code as string (e.g., "996331", "996334")
    
    Returns:
        Decimal: Default GST percentage from mapping, or 0 if not found
    """
    if not sac_code:
        return Decimal('0')
    
    mapping = load_sac_mapping()
    sac_str = str(sac_code).strip()
    
    if sac_str in mapping:
        default_rate = mapping[sac_str].get('default', mapping[sac_str].get('gst_percentage', 0))
        return Decimal(str(default_rate))
    
    return Decimal('0')

def calculate_item_tax(item_subtotal, hsn_code=None, hsn_gst_percentage=None, sac_code=None, sac_gst_percentage=None):
    """
    Calculate tax for an item based on HSN or SAC
    
    Priority:
    1. If vendor has SAC code → use sac_gst_percentage (or default from mapping if not provided)
    2. Else if item has HSN code → use hsn_gst_percentage (or default from mapping if not provided)
    3. Else → 0% tax
    
    Args:
        item_subtotal: Subtotal for the item (Decimal)
        hsn_code: HSN code for the item (optional)
        hsn_gst_percentage: GST percentage for HSN (optional, overrides mapping default)
        sac_code: SAC code for the vendor (optional)
        sac_gst_percentage: GST percentage for SAC (optional, overrides mapping default)
    
    Returns:
        tuple: (tax_amount, gst_percentage)
    """
    # If vendor has SAC, use SAC rate for all items
    if sac_code:
        if sac_gst_percentage is not None:
            gst_percentage = Decimal(str(sac_gst_percentage))
        else:
            # Use default from mapping
            gst_percentage = get_default_gst_from_sac(sac_code)
    # Else use item's HSN code
    elif hsn_code:
        if hsn_gst_percentage is not None:
            gst_percentage = Decimal(str(hsn_gst_percentage))
        else:
            # Use default from mapping
            gst_percentage = get_default_gst_from_hn(hsn_code)
    else:
        gst_percentage = Decimal('0')
    
    # Calculate tax
    tax_amount = (item_subtotal * gst_percentage / 100).quantize(Decimal('0.01'))
    return tax_amount, gst_percentage

