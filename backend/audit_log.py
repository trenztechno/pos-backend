"""
Audit logging utilities for tracking important business events
"""
import logging

audit_logger = logging.getLogger('audit')

def log_vendor_approval(vendor, approved_by, action='approved'):
    """
    Log vendor approval/rejection
    """
    audit_logger.info(
        f"Vendor {action}: {vendor.business_name or vendor.user.username} "
        f"(ID: {vendor.id}) | Approved by: {approved_by.username}",
        extra={
            'event_type': 'vendor_approval',
            'vendor_id': str(vendor.id),
            'vendor_name': vendor.business_name or vendor.user.username,
            'action': action,
            'approved_by': approved_by.username,
        }
    )

def log_item_change(item, user, action='created', changes=None):
    """
    Log item create/update/delete
    """
    audit_logger.info(
        f"Item {action}: {item.name} (ID: {item.id}) | "
        f"Vendor: {item.vendor.business_name if item.vendor else 'None'} | "
        f"Changed by: {user.username if user else 'system'}",
        extra={
            'event_type': 'item_change',
            'item_id': str(item.id),
            'item_name': item.name,
            'vendor_id': str(item.vendor.id) if item.vendor else None,
            'action': action,
            'user': user.username if user else 'system',
            'changes': changes or {},
        }
    )

def log_category_change(category, user, action='created', changes=None):
    """
    Log category create/update/delete
    """
    audit_logger.info(
        f"Category {action}: {category.name} (ID: {category.id}) | "
        f"Vendor: {category.vendor.business_name if category.vendor else 'Global'} | "
        f"Changed by: {user.username if user else 'system'}",
        extra={
            'event_type': 'category_change',
            'category_id': str(category.id),
            'category_name': category.name,
            'vendor_id': str(category.vendor.id) if category.vendor else None,
            'action': action,
            'user': user.username if user else 'system',
            'changes': changes or {},
        }
    )

def log_sales_backup(vendor, device_id, bill_count):
    """
    Log sales backup sync
    """
    audit_logger.info(
        f"Sales backup: {bill_count} bills synced | "
        f"Vendor: {vendor.business_name or vendor.user.username} | "
        f"Device: {device_id}",
        extra={
            'event_type': 'sales_backup',
            'vendor_id': str(vendor.id),
            'device_id': device_id,
            'bill_count': bill_count,
        }
    )

