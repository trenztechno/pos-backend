from django.contrib import admin
from .models import InventoryItem, UnitType

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'current_stock', 'unit_type', 'is_active', 'is_low_stock', 'created_at']
    list_filter = ['is_active', 'unit_type', 'vendor', 'created_at']
    search_fields = ['name', 'description', 'sku', 'barcode', 'supplier', 'location']
    readonly_fields = ['id', 'created_at', 'updated_at', 'is_low_stock', 'stock_status']
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'vendor', 'name', 'description', 'is_active')
        }),
        ('Stock Information', {
            'fields': ('current_stock', 'unit_type', 'min_stock_level', 'max_stock_level', 'is_low_stock', 'stock_status')
        }),
        ('Additional Information', {
            'fields': ('supplier', 'cost_per_unit', 'sku', 'barcode', 'location', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_restocked')
        }),
    )
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'
