from django.contrib import admin
from .models import Item, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'is_active', 'sort_order', 'item_count', 'created_at']
    list_filter = ['is_active', 'vendor', 'created_at']
    search_fields = ['name', 'description', 'vendor__business_name', 'vendor__user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'vendor')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('vendor', 'vendor__user')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'display_categories', 'mrp_price', 'price_type', 'hsn_code', 'hsn_gst_percentage', 'veg_nonveg', 'stock_quantity', 'is_active', 'last_updated']
    list_filter = ['is_active', 'categories', 'vendor', 'price_type', 'veg_nonveg', 'hsn_code', 'created_at']
    search_fields = ['name', 'description', 'sku', 'barcode', 'vendor__business_name']
    readonly_fields = ['id', 'created_at', 'last_updated']
    filter_horizontal = ['categories']  # Better UI for many-to-many
    
    fieldsets = (
        ('Item Information', {
            'fields': ('vendor', 'name', 'description', 'veg_nonveg')
        }),
        ('Categories', {
            'fields': ('categories',),
            'description': 'Items can belong to multiple categories. Select one or more categories for this item.'
        }),
        ('Pricing (HSN/GST Settings)', {
            'fields': ('price', 'mrp_price', 'price_type', 'hsn_code', 'hsn_gst_percentage', 'additional_discount'),
            'description': 'MRP Price is MANDATORY. Price Type: Exclusive (GST not in MRP) or Inclusive (GST in MRP). HSN Code and GST percentage for tax calculation.'
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'sku', 'barcode')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order', 'image'),
            'description': 'Image is optional. Item name will be shown if no image is uploaded.'
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    def display_categories(self, obj):
        """Display categories as comma-separated list"""
        return ", ".join([cat.name for cat in obj.categories.all()])
    display_categories.short_description = 'Categories'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('vendor', 'vendor__user').prefetch_related('categories')
