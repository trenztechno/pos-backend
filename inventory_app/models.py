from django.db import models
from django.core.validators import MinValueValidator
import uuid

class UnitType(models.TextChoices):
    """Unit types for inventory items (raw materials)"""
    KILOGRAM = 'kg', 'Kilogram (kg)'
    GRAM = 'g', 'Gram (g)'
    LITER = 'L', 'Liter (L)'
    MILLILITER = 'mL', 'Milliliter (mL)'
    PIECE = 'pcs', 'Piece (pcs)'
    PACKET = 'pkt', 'Packet (pkt)'
    BOX = 'box', 'Box (box)'
    CARTON = 'carton', 'Carton (carton)'
    BAG = 'bag', 'Bag (bag)'
    BOTTLE = 'bottle', 'Bottle (bottle)'
    CAN = 'can', 'Can (can)'
    DOZEN = 'dozen', 'Dozen (dozen)'
    METER = 'm', 'Meter (m)'
    CENTIMETER = 'cm', 'Centimeter (cm)'
    SQUARE_METER = 'sqm', 'Square Meter (sqm)'
    CUBIC_METER = 'cum', 'Cubic Meter (cum)'

class InventoryItem(models.Model):
    """
    Inventory Item model - for raw materials that vendors use
    This is separate from Item model which is for products that vendors sell
    Each vendor manages their own inventory of raw materials
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('auth_app.Vendor', on_delete=models.CASCADE, related_name='inventory_items')
    name = models.CharField(max_length=255, help_text="Name of the raw material")
    description = models.TextField(blank=True, null=True, help_text="Description of the raw material")
    
    # Stock information
    quantity = models.DecimalField(
        max_digits=15, 
        decimal_places=3, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current stock quantity"
    )
    unit_type = models.CharField(
        max_length=20,
        choices=UnitType.choices,
        default=UnitType.KILOGRAM,
        help_text="Unit of measurement (kg, L, pcs, etc.)"
    )
    
    # Additional information
    sku = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Stock Keeping Unit (optional)"
    )
    barcode = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Barcode (optional)"
    )
    
    # Supplier information (optional)
    supplier_name = models.CharField(max_length=255, blank=True, null=True, help_text="Supplier name")
    supplier_contact = models.CharField(max_length=100, blank=True, null=True, help_text="Supplier contact")
    
    # Reorder information (optional)
    min_stock_level = models.DecimalField(
        max_digits=15, 
        decimal_places=3, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum stock level (alert when below this)"
    )
    reorder_quantity = models.DecimalField(
        max_digits=15, 
        decimal_places=3, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Recommended reorder quantity"
    )
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Whether this inventory item is active")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_restocked_at = models.DateTimeField(blank=True, null=True, help_text="Last time stock was added")
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['vendor', 'is_active']),
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['name']),
        ]
        unique_together = [['vendor', 'name']]  # Same name per vendor (can be changed if needed)
    
    def __str__(self):
        return f"{self.name} ({self.quantity} {self.get_unit_type_display()}) - {self.vendor.business_name}"
    
    @property
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        if self.min_stock_level > 0:
            return self.quantity < self.min_stock_level
        return False
    
    @property
    def needs_reorder(self):
        """Check if item needs reordering"""
        return self.is_low_stock and self.reorder_quantity > 0
