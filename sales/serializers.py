from rest_framework import serializers
from .models import Bill, BillItem, SalesBackup
from items.models import Item

class BillItemSerializer(serializers.ModelSerializer):
    """Serializer for individual bill items"""
    item_name = serializers.CharField(required=True)
    original_item_id = serializers.UUIDField(required=False, allow_null=True)
    item_id = serializers.UUIDField(required=False, allow_null=True, source='original_item_id', help_text="Alias for original_item_id (for mobile compatibility)")
    
    class Meta:
        model = BillItem
        fields = [
            'id', 'bill', 'item', 'original_item_id', 'item_id', 'item_name', 'item_description',
            'price', 'mrp_price', 'price_type', 'quantity', 'subtotal',
            'gst_percentage', 'item_gst_amount', 'veg_nonveg',
            'additional_discount', 'discount_amount', 'unit',
            'batch_number', 'expiry_date', 'created_at'
        ]
        read_only_fields = ['id', 'bill', 'created_at']

class BillSerializer(serializers.ModelSerializer):
    """Serializer for Bill model"""
    items = BillItemSerializer(many=True, read_only=True)
    items_data = BillItemSerializer(many=True, write_only=True, required=False, help_text="Items to create with this bill")
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    total_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = Bill
        fields = [
            'id', 'vendor', 'vendor_name', 'device_id',
            'invoice_number', 'bill_number', 'bill_date',
            'restaurant_name', 'address', 'gstin', 'fssai_license', 'logo_url', 'footer_note',
            'customer_name', 'customer_phone', 'customer_email', 'customer_address',
            'billing_mode', 'subtotal', 'total_amount',
            'total_tax', 'cgst_amount', 'sgst_amount', 'igst_amount',
            'payment_mode', 'payment_reference', 'amount_paid', 'change_amount',
            'discount_amount', 'discount_percentage',
            'notes', 'table_number', 'waiter_name',
            'items', 'items_data', 'item_count', 'total_quantity',
            'created_at', 'synced_at', 'updated_at'
        ]
        read_only_fields = ['id', 'vendor', 'synced_at', 'updated_at']
    
    def get_total_quantity(self, obj):
        """Calculate total quantity of all items"""
        return sum(item.quantity for item in obj.items.all())
    
    def create(self, validated_data):
        """Create bill with items"""
        items_data = validated_data.pop('items_data', [])
        bill = Bill.objects.create(**validated_data)
        
        # Create bill items
        for item_data in items_data:
            BillItem.objects.create(bill=bill, **item_data)
        
        return bill
    
    def update(self, instance, validated_data):
        """Update bill (items are typically not updated after creation)"""
        items_data = validated_data.pop('items_data', None)
        
        # Update bill fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # If items_data provided, update items (optional - usually bills are immutable)
        if items_data is not None:
            # Delete existing items and create new ones
            instance.items.all().delete()
            for item_data in items_data:
                BillItem.objects.create(bill=instance, **item_data)
        
        return instance


class BillListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing bills"""
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = Bill
        fields = [
            'id', 'invoice_number', 'bill_number', 'bill_date',
            'billing_mode', 'total_amount', 'item_count',
            'payment_mode', 'vendor_name', 'created_at', 'synced_at'
        ]


# Legacy serializer (for backward compatibility)
class SalesBackupSerializer(serializers.ModelSerializer):
    """DEPRECATED: Use BillSerializer instead"""
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    
    class Meta:
        model = SalesBackup
        fields = ['id', 'vendor', 'vendor_name', 'bill_data', 'device_id', 'synced_at', 'created_at']
        read_only_fields = ['id', 'vendor', 'synced_at', 'created_at']
