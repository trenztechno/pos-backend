from rest_framework import serializers
from .models import InventoryItem, UnitType

class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for InventoryItem with full details"""
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    needs_reorder = serializers.BooleanField(read_only=True)
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id',
            'vendor',
            'vendor_name',
            'name',
            'description',
            'quantity',
            'unit_type',
            'unit_type_display',
            'sku',
            'barcode',
            'supplier_name',
            'supplier_contact',
            'min_stock_level',
            'reorder_quantity',
            'is_active',
            'is_low_stock',
            'needs_reorder',
            'created_at',
            'updated_at',
            'last_restocked_at',
        ]
        read_only_fields = ['id', 'vendor', 'vendor_name', 'created_at', 'updated_at', 'is_low_stock', 'needs_reorder']
    
    def validate_quantity(self, value):
        """Ensure quantity is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value
    
    def validate_min_stock_level(self, value):
        """Ensure min_stock_level is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Minimum stock level cannot be negative")
        return value
    
    def validate_reorder_quantity(self, value):
        """Ensure reorder_quantity is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Reorder quantity cannot be negative")
        return value

class InventoryItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing inventory items"""
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    needs_reorder = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id',
            'name',
            'quantity',
            'unit_type',
            'unit_type_display',
            'sku',
            'is_active',
            'is_low_stock',
            'needs_reorder',
            'updated_at',
        ]

class InventoryStockUpdateSerializer(serializers.Serializer):
    """Serializer for updating stock quantity"""
    quantity = serializers.DecimalField(
        max_digits=15, 
        decimal_places=3, 
        required=True,
        help_text="New stock quantity"
    )
    action = serializers.ChoiceField(
        choices=['set', 'add', 'subtract'],
        default='set',
        help_text="'set' to set exact quantity, 'add' to add to current, 'subtract' to subtract from current"
    )
    notes = serializers.CharField(
        max_length=500, 
        required=False, 
        allow_blank=True,
        help_text="Optional notes about this stock update"
    )
    
    def validate_quantity(self, value):
        """Ensure quantity is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value

