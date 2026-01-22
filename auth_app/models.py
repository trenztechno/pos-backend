from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid
import os

def vendor_logo_upload_path(instance, filename):
    """Generate upload path for vendor logos: media/vendors/{vendor_id}/logo.{ext}"""
    ext = filename.split('.')[-1]
    filename = f"logo.{ext}"
    return os.path.join('vendors', str(instance.id), filename)

class Vendor(models.Model):
    """
    Vendor model - represents vendors who register and use the POS system
    Separate from User model which is for server administrators
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    business_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gst_no = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="GST Number (GSTIN) for password reset and bills")
    fssai_license = models.CharField(max_length=50, blank=True, null=True, help_text="FSSAI License Number (required for restaurant bills)")
    logo = models.ImageField(
        upload_to=vendor_logo_upload_path,
        blank=True,
        null=True,
        help_text="Restaurant/Vendor logo (JPG, PNG, WebP)",
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])
        ]
    )
    footer_note = models.TextField(blank=True, null=True, help_text="Footer note to be displayed on bills (e.g., 'Thank you for visiting!')")
    is_approved = models.BooleanField(default=False)  # Admin approval status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['gst_no']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.business_name or 'No Business Name'}"

class SalesRep(models.Model):
    """
    Sales Rep model - represents sales representatives who can approve vendors
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sales_rep_profile')
    name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.name or 'Sales Rep'}"
