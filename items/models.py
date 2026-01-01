from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('auth_app.Vendor', on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    categories = models.ManyToManyField(Category, related_name='items', blank=True, help_text="Items can belong to multiple categories")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    sku = models.CharField(max_length=100, blank=True, null=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0, help_text="Lower numbers appear first")
    image = models.ImageField(
        upload_to=item_image_upload_path,
        blank=True,
        null=True,
        help_text="Item image (JPG, PNG, WebP)",
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
