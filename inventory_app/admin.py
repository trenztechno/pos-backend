from django.contrib import admin
from .models import InventoryItem, UnitType

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'quantity', 'unit_type', 'is_active', 'is_low_stock', 'created_at']
    list_filter = ['is_active', 'unit_type', 'vendor', 'created_at']
    search_fields = ['name', 'description', 'sku', 'barcode', 'supplier_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'is_low_stock', 'needs_reorder']
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'vendor', 'name', 'description')
        }),
        ('Stock Information', {
            'fields': ('quantity', 'unit_type', 'min_stock_level', 'reorder_quantity', 'is_low_stock', 'needs_reorder')
        }),
        ('Additional Information', {
            'fields': ('sku', 'barcode', 'supplier_name', 'supplier_contact')
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'last_restocked_at', 'created_at', 'updated_at')
        }),
    )
