from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django import forms
from .models import Vendor, VendorUser

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

class VendorUserInline(admin.TabularInline):
    """Inline admin for managing vendor staff users"""
    model = VendorUser
    extra = 0
    fields = ('user', 'is_owner', 'is_active', 'created_at', 'created_by')
    readonly_fields = ('created_at',)
    autocomplete_fields = ['user', 'created_by']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'created_by')


class SecurityPINForm(forms.ModelForm):
    """Custom form for security PIN management"""
    security_pin_display = forms.CharField(
        label='Security PIN',
        required=False,
        help_text='Enter new PIN to set/change (leave blank to keep current, enter new PIN to change)',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter new PIN (min 4 digits)'}),
    )
    security_pin_clear = forms.BooleanField(
        label='Clear Security PIN',
        required=False,
        help_text='Check to remove security PIN',
    )
    
    class Meta:
        model = Vendor
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['security_pin_display'].help_text = 'Leave blank to keep current PIN, or enter new PIN to change it'
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle PIN clearing
        if self.cleaned_data.get('security_pin_clear'):
            instance.set_security_pin(None)
        # Handle PIN setting/changing
        elif self.cleaned_data.get('security_pin_display'):
            new_pin = self.cleaned_data['security_pin_display']
            if len(new_pin) >= 4:
                instance.set_security_pin(new_pin)
            else:
                from django.core.exceptions import ValidationError
                raise ValidationError('Security PIN must be at least 4 characters')
        
        if commit:
            instance.save()
        return instance


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """
    Vendor Admin - For managing vendors who register to use the POS system
    This is where you approve vendors and manage their staff users!
    """
    form = SecurityPINForm
    list_display = ['id', 'business_name', 'username', 'email', 'phone', 'approval_status', 'has_pin_display', 'staff_count', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['business_name', 'user__username', 'user__email', 'phone', 'gst_no']
    readonly_fields = ['id', 'created_at', 'updated_at', 'logo_preview', 'security_pin_status']
    inlines = [VendorUserInline]
    actions = ['approve_vendors', 'reject_vendors']
    
    def logo_preview(self, obj):
        """Display logo preview in admin"""
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.logo.url)
        return "No logo uploaded"
    logo_preview.short_description = 'Logo Preview'
    
    def security_pin_status(self, obj):
        """Display security PIN status"""
        if obj.has_security_pin():
            return format_html('<span style="color: green; font-weight: bold;">✓ PIN Set</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">⚠ No PIN Set</span>')
    security_pin_status.short_description = 'Security PIN Status'
    
    def has_pin_display(self, obj):
        """Display PIN status in list view"""
        return obj.has_security_pin()
    has_pin_display.short_description = 'PIN'
    has_pin_display.boolean = True
    
    def staff_count(self, obj):
        """Count of staff users"""
        count = obj.vendor_users.filter(is_active=True, is_owner=False).count()
        return count
    staff_count.short_description = 'Staff Users'
    
    fieldsets = (
        ('Vendor Information', {
            'fields': ('user', 'business_name', 'phone', 'address')
        }),
        ('License & Registration', {
            'fields': ('gst_no', 'fssai_license'),
            'description': 'GST number (GSTIN) is used for password reset and bills. FSSAI License is required for restaurant bills.'
        }),
        ('Bill Customization', {
            'fields': ('logo', 'footer_note', 'bill_prefix', 'bill_starting_number', 'last_bill_number'),
            'description': 'Logo and footer note will appear on all bills. Logo is optional. Bill numbering configuration for sequential invoice numbers.'
        }),
        ('SAC Code (Service Accounting Code)', {
            'fields': ('sac_code', 'sac_gst_percentage'),
            'description': 'SAC code for vendor-level GST. If set, all items use this SAC GST rate instead of their HSN codes. Leave blank to use item-level HSN codes.',
            'classes': ('collapse',)
        }),
        ('Security PIN Management', {
            'fields': ('security_pin_status', 'security_pin_display', 'security_pin_clear'),
            'description': 'Security PIN is required for vendor owner to manage staff users. Set a PIN to enable staff management features.'
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
        return qs.prefetch_related('vendor_users').order_by('is_approved', '-created_at')


@admin.register(VendorUser)
class VendorUserAdmin(admin.ModelAdmin):
    """
    VendorUser Admin - Manage vendor staff users
    """
    list_display = ['id', 'vendor', 'user', 'role_display', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_owner', 'is_active', 'created_at']
    search_fields = ['vendor__business_name', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at']
    autocomplete_fields = ['vendor', 'user', 'created_by']
    
    def role_display(self, obj):
        """Display role with color coding"""
        if obj.is_owner:
            return format_html('<span style="color: blue; font-weight: bold;">👑 Owner</span>')
        else:
            return format_html('<span style="color: green;">👤 Staff</span>')
    role_display.short_description = 'Role'
    
    fieldsets = (
        ('User Information', {
            'fields': ('vendor', 'user', 'is_owner', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('vendor', 'user', 'created_by')
