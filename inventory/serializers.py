from rest_framework import serializers
from .models import InventoryItem, UnitType

class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for InventoryItem with full details"""
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_status = serializers.CharField(read_only=True)
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id',
            'vendor',
            'vendor_name',
            'name',
            'description',
            'current_stock',
            'unit_type',
            'unit_type_display',
            'min_stock_level',
            'max_stock_level',
            'supplier',
            'cost_per_unit',
            'sku',
            'barcode',
            'location',
            'is_active',
            'is_low_stock',
            'stock_status',
            'notes',
            'created_at',
            'updated_at',
            'last_restocked',
        ]
        read_only_fields = ['id', 'vendor', 'created_at', 'updated_at', 'is_low_stock', 'stock_status', 'vendor_name']
    
    def validate_unit_type(self, value):
        """Validate unit type is in allowed choices"""
        if value not in [choice[0] for choice in UnitType.choices]:
            raise serializers.ValidationError(f"Invalid unit type. Must be one of: {', '.join([c[0] for c in UnitType.choices])}")
        return value
    
    def validate(self, data):
        """Validate stock levels"""
        min_stock = data.get('min_stock_level', self.instance.min_stock_level if self.instance else 0)
        max_stock = data.get('max_stock_level', self.instance.max_stock_level if self.instance else None)
        
        if max_stock is not None and min_stock > max_stock:
            raise serializers.ValidationError({
                'max_stock_level': 'Maximum stock level must be greater than or equal to minimum stock level'
            })
        
        return data

class InventoryItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing inventory items"""
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_status = serializers.CharField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id',
            'name',
            'current_stock',
            'unit_type',
            'unit_type_display',
            'min_stock_level',
            'is_low_stock',
            'stock_status',
            'location',
            'is_active',
            'updated_at',
        ]

class StockUpdateSerializer(serializers.Serializer):
    """Serializer for updating stock quantity"""
    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=3,
        required=True,
        help_text="Quantity to add (positive) or subtract (negative)"
    )
    notes = serializers.CharField(required=False, allow_blank=True, help_text="Optional notes for this stock update")

