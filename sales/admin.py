from django.contrib import admin
from .models import Bill, BillItem, SalesBackup

class BillItemInline(admin.TabularInline):
    """Inline admin for bill items"""
    model = BillItem
    extra = 0
    readonly_fields = ['id', 'created_at']
    fields = ['item', 'item_name', 'quantity', 'price', 'mrp_price', 'subtotal', 'gst_percentage', 'item_gst_amount', 'veg_nonveg']
    can_delete = False  # Bills are typically immutable

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'vendor', 'bill_date', 'billing_mode', 'total_amount', 'item_count', 'payment_mode', 'synced_at']
    list_filter = ['billing_mode', 'payment_mode', 'bill_date', 'synced_at', 'vendor']
    search_fields = ['invoice_number', 'bill_number', 'customer_name', 'customer_phone', 'vendor__business_name']
    readonly_fields = ['id', 'created_at', 'synced_at', 'updated_at', 'item_count', 'total_quantity']
    inlines = [BillItemInline]
    date_hierarchy = 'bill_date'
    
    fieldsets = (
        ('Bill Information', {
            'fields': ('vendor', 'invoice_number', 'bill_number', 'bill_date', 'device_id')
        }),
        ('Bill Header (for Printing)', {
            'fields': ('restaurant_name', 'address', 'gstin', 'fssai_license', 'logo_url', 'footer_note')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone', 'customer_email', 'customer_address'),
            'classes': ('collapse',)
        }),
        ('Billing Details', {
            'fields': ('billing_mode', 'subtotal', 'total_amount', 'total_tax', 'cgst_amount', 'sgst_amount', 'igst_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_mode', 'payment_reference', 'amount_paid', 'change_amount')
        }),
        ('Discounts', {
            'fields': ('discount_percentage',),
            'description': 'Discount is percentage-based, applied to subtotal (before tax). discount_amount is calculated automatically as a property.',
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'table_number', 'waiter_name'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('item_count', 'total_quantity'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'synced_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'

@admin.register(BillItem)
class BillItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'bill', 'quantity', 'price', 'subtotal', 'gst_percentage', 'item_gst_amount', 'created_at']
    list_filter = ['veg_nonveg', 'price_type', 'created_at']
    search_fields = ['item_name', 'bill__invoice_number', 'bill__vendor__business_name']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Item Information', {
            'fields': ('bill', 'item', 'item_id', 'item_name', 'item_description')
        }),
        ('Pricing', {
            'fields': ('price', 'mrp_price', 'price_type', 'quantity', 'subtotal')
        }),
        ('Tax Information', {
            'fields': ('gst_percentage', 'item_gst_amount', 'veg_nonveg')
        }),
        # Item-level discounts removed - discounts are now bill-level percentage only
        ('Additional Information', {
            'fields': ('unit', 'batch_number', 'expiry_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SalesBackup)
class SalesBackupAdmin(admin.ModelAdmin):
    """DEPRECATED: Legacy model admin"""
    list_display = ['id', 'vendor', 'device_id', 'synced_at', 'created_at']
    list_filter = ['synced_at', 'created_at', 'vendor']
    search_fields = ['device_id', 'vendor__business_name']
    readonly_fields = ['id', 'synced_at', 'created_at']
    
    fieldsets = (
        ('Legacy Bill Data', {
            'fields': ('vendor', 'device_id', 'bill_data'),
            'description': 'DEPRECATED: This model is kept for backward compatibility. Use Bill model instead.'
        }),
        ('Timestamps', {
            'fields': ('id', 'synced_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )
