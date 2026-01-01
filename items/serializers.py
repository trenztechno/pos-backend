from rest_framework import serializers
from .models import Item, Category
from auth_app.models import Vendor

class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'sort_order', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ItemSerializer(serializers.ModelSerializer):
    categories_list = serializers.SerializerMethodField()
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        source='categories',
        required=False,
        allow_empty=True
    )
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = [
            'id', 'vendor', 'categories', 'category_ids', 'categories_list',
            'name', 'description', 'price', 'stock_quantity', 'sku', 'barcode',
            'is_active', 'sort_order', 'vendor_name', 'image', 'image_url',
            'last_updated', 'created_at'
        ]
        read_only_fields = ['id', 'vendor', 'last_updated', 'created_at']
    
    def get_categories_list(self, obj):
        """Return list of category names for this item"""
        return [{'id': str(cat.id), 'name': cat.name} for cat in obj.categories.all()]
    
    def get_image_url(self, obj):
        """Return full URL to item image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class ItemListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    categories_list = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = ['id', 'name', 'price', 'stock_quantity', 'is_active', 'categories_list', 'sort_order', 'image_url']
    
    def get_categories_list(self, obj):
        """Return list of category names"""
        return [cat.name for cat in obj.categories.all()]
    
    def get_image_url(self, obj):
        """Return full URL to item image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
