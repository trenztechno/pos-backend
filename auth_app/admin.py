from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Vendor

# Unregister default User admin if it exists
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Keep User admin for server administrators (simplified)
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    User Admin - For server administrators only
    Vendors are managed separately in Vendor admin
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_queryset(self, request):
        """Show only users who are NOT vendors (staff/superusers)"""
        qs = super().get_queryset(request)
        # Filter to show staff/superusers or users without vendor profiles
        return qs.filter(is_staff=True) | qs.filter(vendor_profile__isnull=True)

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """
    Vendor Admin - For managing vendors who register to use the POS system
    This is where you approve vendors!
    """
    list_display = ['id', 'business_name', 'username', 'email', 'phone', 'approval_status', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['business_name', 'user__username', 'user__email', 'phone']
    readonly_fields = ['id', 'created_at', 'updated_at', 'logo_preview']
    
    def logo_preview(self, obj):
        """Display logo preview in admin"""
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.logo.url)
        return "No logo uploaded"
    logo_preview.short_description = 'Logo Preview'
    actions = ['approve_vendors', 'reject_vendors']
    
    fieldsets = (
        ('Vendor Information', {
            'fields': ('user', 'business_name', 'phone', 'address')
        }),
        ('License & Registration', {
            'fields': ('gst_no', 'fssai_license'),
            'description': 'GST number (GSTIN) is used for password reset and bills. FSSAI License is required for restaurant bills.'
        }),
        ('Bill Customization', {
            'fields': ('logo', 'footer_note'),
            'description': 'Logo and footer note will appear on all bills. Logo is optional.'
        }),
        ('Approval Status', {
            'fields': ('is_approved',),
            'description': '✓ Check "Approved" to approve vendor. Unapproved vendors cannot login until approved.'
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def username(self, obj):
        return obj.user.username
    username.short_description = 'Username'
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    
    def approval_status(self, obj):
        if obj.is_approved and obj.user.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Approved</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">⏳ Pending Approval</span>')
    approval_status.short_description = 'Approval Status'
    
    def approve_vendors(self, request, queryset):
        """Approve selected vendors - makes them active and approved"""
        count = 0
        for vendor in queryset:
            vendor.is_approved = True
            vendor.user.is_active = True
            vendor.user.save()
            vendor.save()
            count += 1
        self.message_user(request, f'✓ {count} vendor(s) approved successfully. They can now login.')
    approve_vendors.short_description = '✓ Approve selected vendors'
    
    def reject_vendors(self, request, queryset):
        """Reject/Deactivate selected vendors"""
        count = 0
        for vendor in queryset:
            vendor.is_approved = False
            vendor.user.is_active = False
            vendor.user.save()
            vendor.save()
            count += 1
        self.message_user(request, f'✗ {count} vendor(s) rejected/deactivated.')
    reject_vendors.short_description = '✗ Reject/Deactivate selected vendors'
    
    def get_queryset(self, request):
        """Show pending vendors first"""
        qs = super().get_queryset(request)
        return qs.order_by('is_approved', '-created_at')
