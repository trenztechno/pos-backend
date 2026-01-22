from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid

class Bill(models.Model):
    """
    Bill Model - Structured storage for sales transactions
    Extendable for future business logic (analytics, inventory deduction, etc.)
    """
    BILLING_MODE_CHOICES = [
        ('gst', 'GST'),
        ('non_gst', 'Non-GST'),
    ]
    
    PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('auth_app.Vendor', on_delete=models.CASCADE, related_name='bills')
    device_id = models.CharField(max_length=255, blank=True, null=True, help_text="Device that created this bill")
    
    # Bill Identifiers (from mobile app)
    invoice_number = models.CharField(max_length=100, help_text="Auto-generated invoice number (e.g., INV-2024-001)")
    bill_number = models.CharField(max_length=100, blank=True, null=True, help_text="Bill number")
    bill_date = models.DateField(help_text="Date of the bill")
    
    # Bill Header Information (for printing)
    restaurant_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gstin = models.CharField(max_length=50, blank=True, null=True, help_text="GSTIN for this bill")
    fssai_license = models.CharField(max_length=50, blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True, help_text="Logo URL for bill printing")
    footer_note = models.TextField(blank=True, null=True, help_text="Footer note for bill")
    
    # Customer Information (Extendable)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)
    
    # Billing Mode
    billing_mode = models.CharField(max_length=20, choices=BILLING_MODE_CHOICES, default='gst')
    
    # Financial Summary
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], help_text="Subtotal before tax")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], help_text="Final total amount")
    
    # Tax Breakdown (for GST bills)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="Total tax amount")
    cgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="CGST amount (for intra-state)")
    sgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="SGST amount (for intra-state)")
    igst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="IGST amount (for inter-state)")
    
    # Payment Information (Extendable)
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODE_CHOICES, default='cash')
    payment_reference = models.CharField(max_length=255, blank=True, null=True, help_text="Transaction ID, cheque number, etc.")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    change_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="Change given to customer")
    
    # Discounts (Extendable)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="Total discount amount")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="Discount percentage")
    
    # Additional Fields (Extendable)
    notes = models.TextField(blank=True, null=True, help_text="Additional notes for this bill")
    table_number = models.CharField(max_length=50, blank=True, null=True, help_text="Table number (for restaurants)")
    waiter_name = models.CharField(max_length=255, blank=True, null=True, help_text="Waiter/server name")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="When bill was created on mobile")
    synced_at = models.DateTimeField(auto_now=True, help_text="When bill was synced to server")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update time")
    
    class Meta:
        ordering = ['-synced_at', '-created_at']
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['vendor', 'synced_at']),
            models.Index(fields=['vendor', 'bill_date']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['billing_mode']),
            models.Index(fields=['device_id']),
        ]
        # Prevent duplicate bills with same invoice number from same vendor
        unique_together = [['vendor', 'invoice_number']]
    
    def __str__(self):
        return f"Bill {self.invoice_number} - {self.vendor.business_name or self.vendor.user.username} (₹{self.total_amount})"
    
    @property
    def item_count(self):
        """Get total number of items in this bill"""
        return self.items.count()
    
    @property
    def total_quantity(self):
        """Get total quantity of all items"""
        return sum(item.quantity for item in self.items.all())


class BillItem(models.Model):
    """
    BillItem Model - Individual line items in a bill
    Stores snapshot of item details at time of sale (for historical accuracy)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    
    # Link to master Item (optional - item might be deleted later)
    item = models.ForeignKey('items.Item', on_delete=models.SET_NULL, null=True, blank=True, related_name='bill_items', help_text="Link to master Item (if exists)")
    
    # Snapshot of item details at time of sale (for historical accuracy)
    original_item_id = models.UUIDField(blank=True, null=True, help_text="Original item ID from mobile (UUID string)")
    item_name = models.CharField(max_length=255, help_text="Item name at time of sale")
    item_description = models.TextField(blank=True, null=True, help_text="Item description at time of sale")
    
    # Pricing (snapshot at time of sale)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Unit price at time of sale")
    mrp_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="MRP at time of sale")
    price_type = models.CharField(max_length=20, choices=[('exclusive', 'Exclusive'), ('inclusive', 'Inclusive')], default='exclusive', help_text="Price type at time of sale")
    
    # Quantity and Calculations
    quantity = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)], help_text="Quantity sold (supports decimals like 1.5 kg)")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], help_text="Subtotal for this item (quantity * price)")
    
    # Tax Information (for GST bills)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="GST percentage at time of sale")
    item_gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="GST amount for this item")
    
    # Additional Information
    veg_nonveg = models.CharField(max_length=10, choices=[('veg', 'Veg'), ('non_veg', 'Non-Veg')], blank=True, null=True, help_text="Veg/Non-veg at time of sale")
    additional_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="Additional discount on this item")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="Discount amount for this item")
    
    # Extendable fields
    unit = models.CharField(max_length=50, blank=True, null=True, help_text="Unit of measurement (kg, pcs, etc.)")
    batch_number = models.CharField(max_length=100, blank=True, null=True, help_text="Batch number (for inventory tracking)")
    expiry_date = models.DateField(blank=True, null=True, help_text="Expiry date (for inventory tracking)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['bill', 'created_at']),
            models.Index(fields=['item']),
            models.Index(fields=['original_item_id'], name='billitem_original_item_id_idx'),
        ]
    
    def __str__(self):
        return f"{self.item_name} x {self.quantity} = ₹{self.subtotal} (Bill: {self.bill.invoice_number})"
    
    @property
    def total_with_tax(self):
        """Get total including tax for this item"""
        return self.subtotal + self.item_gst_amount


# Keep SalesBackup for backward compatibility (deprecated, use Bill instead)
class SalesBackup(models.Model):
    """
    DEPRECATED: Use Bill and BillItem models instead
    Kept for backward compatibility and migration purposes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('auth_app.Vendor', on_delete=models.CASCADE, related_name='sales_backups', null=True, blank=True)
    bill_data = models.JSONField(help_text="DEPRECATED: Use Bill model instead")
    device_id = models.CharField(max_length=255, blank=True, null=True)
    synced_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-synced_at']
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['vendor', 'synced_at']),
            models.Index(fields=['device_id']),
        ]
    
    def __str__(self):
        return f"Legacy Bill {self.id} from {self.vendor.business_name or self.vendor.user.username if self.vendor else 'Unknown'} ({self.device_id or 'Unknown'})"
