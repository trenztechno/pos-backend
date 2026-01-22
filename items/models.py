from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
import uuid
import os

def item_image_upload_path(instance, filename):
    """Generate upload path for item images: media/items/{item_id}/{filename}"""
    ext = filename.split('.')[-1]
    filename = f"{instance.id}.{ext}"
    return os.path.join('items', str(instance.id), filename)

class Category(models.Model):
    """
    Category model - for organizing items (drinks, breakfast, lunch, etc.)
    Categories can be vendor-specific or global
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    vendor = models.ForeignKey('auth_app.Vendor', on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    # If vendor is None, it's a global category available to all vendors
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0, help_text="Lower numbers appear first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['vendor', 'is_active']),
            models.Index(fields=['sort_order']),
        ]
        unique_together = [['name', 'vendor']]  # Same category name per vendor
    
    def __str__(self):
        vendor_name = self.vendor.business_name if self.vendor else "Global"
        return f"{self.name} ({vendor_name})"

class Item(models.Model):
    VEG_NONVEG_CHOICES = [
        ('veg', 'Vegetarian'),
        ('nonveg', 'Non-Vegetarian'),
    ]
    
    PRICE_TYPE_CHOICES = [
        ('exclusive', 'Exclusive (GST not included in MRP)'),
        ('inclusive', 'Inclusive (GST included in MRP)'),
    ]
    
    GST_PERCENTAGE_CHOICES = [
        (0, '0%'),
        (5, '5%'),
        (8, '8%'),
        (18, '18%'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('auth_app.Vendor', on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    categories = models.ManyToManyField(Category, related_name='items', blank=True, help_text="Items can belong to multiple categories")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Pricing fields
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Base price")
    mrp_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)], help_text="MRP Price (Exclusive or Inclusive based on price_type) - MANDATORY for new items")
    price_type = models.CharField(max_length=10, choices=PRICE_TYPE_CHOICES, default='exclusive', help_text="Exclusive: GST not included in MRP. Inclusive: GST included in MRP")
    additional_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], help_text="Additional discount amount (optional)")
    
    # GST fields
    gst_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="GST percentage (0%, 5%, 8%, 18%, or custom) - Not compulsory for item creation"
    )
    
    # Food type
    veg_nonveg = models.CharField(max_length=10, choices=VEG_NONVEG_CHOICES, blank=True, null=True, help_text="Vegetarian or Non-Vegetarian")
    
    # Inventory
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    sku = models.CharField(max_length=100, blank=True, null=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0, help_text="Lower numbers appear first")
    
    # Image (optional)
    image = models.ImageField(
        upload_to=item_image_upload_path,
        blank=True,
        null=True,
        help_text="Item image (JPG, PNG, WebP) - Optional. Item name shown if no image",
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])
        ]
    )
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['vendor', 'is_active']),
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.vendor.business_name or self.vendor.user.username if self.vendor else 'No Vendor'}"
