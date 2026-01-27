from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
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
    # Primary owner account for this vendor (created during registration)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    business_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gst_no = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="GST Number (GSTIN) for password reset and bills",
    )
    fssai_license = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="FSSAI License Number (required for restaurant bills)",
    )
    logo = models.ImageField(
        upload_to=vendor_logo_upload_path,
        blank=True,
        null=True,
        help_text="Restaurant/Vendor logo (JPG, PNG, WebP)",
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])
        ],
    )
    footer_note = models.TextField(
        blank=True,
        null=True,
        help_text="Footer note to be displayed on bills (e.g., 'Thank you for visiting!')",
    )
    security_pin = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Hashed security PIN for accessing sensitive operations (user management, etc.)",
    )
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

    @classmethod
    def get_vendor_for_user(cls, user):
        """
        Get vendor for a given user.

        - If user is the primary owner (vendor_profile), return that vendor
        - Else, if user is linked via VendorUser (staff), return that vendor
        - Else, return None
        """
        # Primary owner relationship (existing behavior)
        try:
            return user.vendor_profile
        except cls.DoesNotExist:
            pass
        except AttributeError:
            # user has no vendor_profile relation
            pass

        # Staff/secondary accounts via VendorUser
        try:
            # Avoid circular import by using reverse relation name
            membership = user.vendor_memberships.filter(is_active=True).select_related('vendor').first()
            if membership:
                return membership.vendor
        except Exception:
            pass

        return None

    def is_user_owner(self, user):
        """
        Check if the given user is the owner/admin of this vendor.

        - Primary owner: vendor.user
        - Or any VendorUser with is_owner=True
        """
        if user == self.user:
            return True

        try:
            membership = self.vendor_users.filter(user=user, is_active=True).first()
            if membership and membership.is_owner:
                return True
        except Exception:
            pass

        return False

    def set_security_pin(self, pin):
        """Set security PIN (hashed)"""
        if not pin:
            self.security_pin = None
        else:
            self.security_pin = make_password(pin)
        self.save()

    def check_security_pin(self, pin):
        """Verify security PIN"""
        if not self.security_pin:
            return False
        return check_password(pin, self.security_pin)

    def has_security_pin(self):
        """Check if security PIN is set"""
        return bool(self.security_pin)


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


class VendorUser(models.Model):
    """
    Link table between Vendor and User to support multiple users per vendor.

    - is_owner=True: vendor admin (can manage staff users)
    - is_owner=False: staff user (can perform billing, cannot manage users)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='vendor_users',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vendor_memberships',
    )
    is_owner = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_vendor_users',
        help_text="Vendor owner who created this user",
    )

    class Meta:
        unique_together = [['vendor', 'user']]
        indexes = [
            models.Index(fields=['vendor', 'user']),
            models.Index(fields=['vendor', 'is_active']),
            models.Index(fields=['vendor', 'is_owner']),
        ]

    def __str__(self):
        role = 'Owner' if self.is_owner else 'Staff'
        return f"{self.user.username} ({role}) -> {self.vendor.business_name or self.vendor.user.username}"

