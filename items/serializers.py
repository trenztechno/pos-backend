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
            'name', 'description', 'price', 'mrp_price', 'price_type', 'additional_discount',
            'gst_percentage', 'veg_nonveg',
            'stock_quantity', 'sku', 'barcode',
            'is_active', 'sort_order', 'vendor_name', 'image', 'image_url',
            'last_updated', 'created_at'
        ]
        read_only_fields = ['id', 'vendor', 'last_updated', 'created_at']
    
    def get_categories_list(self, obj):
        """Return list of category names for this item"""
        return [{'id': str(cat.id), 'name': cat.name} for cat in obj.categories.all()]
    
    def get_image_url(self, obj):
        """Return full URL to item image (works with both local and S3 storage)"""
        if obj.image:
            # For S3, obj.image.url already returns full URL
            # For local, obj.image.url returns relative path
            image_url = obj.image.url
            if image_url.startswith('http://') or image_url.startswith('https://'):
                # Already a full URL (S3)
                return image_url
            else:
                # Relative path (local storage) - build absolute URL
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(image_url)
                return image_url
        return None
    
class ItemListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    categories_list = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = ['id', 'name', 'price', 'mrp_price', 'price_type', 'gst_percentage', 'veg_nonveg', 
                  'stock_quantity', 'is_active', 'categories_list', 'sort_order', 'image_url']
    
    def get_categories_list(self, obj):
        """Return list of category names"""
        return [cat.name for cat in obj.categories.all()]
    
    def get_image_url(self, obj):
        """Return full URL to item image (works with both local and S3 storage)"""
        if obj.image:
            # For S3, obj.image.url already returns full URL
            # For local, obj.image.url returns relative path
            image_url = obj.image.url
            if image_url.startswith('http://') or image_url.startswith('https://'):
                # Already a full URL (S3)
                return image_url
            else:
                # Relative path (local storage) - build absolute URL
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(image_url)
                return image_url
        return None
