from rest_framework import serializers
from django.conf import settings
from django.db.models import Q
from .models import Item, Category
from auth_app.models import Vendor
from backend.s3_utils import generate_presigned_url

class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'sort_order', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ItemSerializer(serializers.ModelSerializer):
    categories_list = serializers.SerializerMethodField()
    category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True
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
        """Return full URL to item image (works with both local and S3 storage)
        Uses pre-signed URLs for S3 when enabled (more secure, no public bucket needed)"""
        if obj.image:
            # Check if using S3 with pre-signed URLs
            if settings.USE_S3 and getattr(settings, 'USE_S3_PRESIGNED_URLS', True):
                presigned_url = generate_presigned_url(obj.image)
                if presigned_url:
                    return presigned_url
            
            # For S3 without pre-signed URLs, or local storage
            image_url = obj.image.url
            if image_url.startswith('http://') or image_url.startswith('https://'):
                # Already a full URL (S3 public URL)
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
        """Return full URL to item image (works with both local and S3 storage)
        Uses pre-signed URLs for S3 when enabled (more secure, no public bucket needed)"""
        if obj.image:
            # Check if using S3 with pre-signed URLs
            if settings.USE_S3 and getattr(settings, 'USE_S3_PRESIGNED_URLS', True):
                presigned_url = generate_presigned_url(obj.image)
                if presigned_url:
                    return presigned_url
            
            # For S3 without pre-signed URLs, or local storage
            image_url = obj.image.url
            if image_url.startswith('http://') or image_url.startswith('https://'):
                # Already a full URL (S3 public URL)
                return image_url
            else:
                # Relative path (local storage) - build absolute URL
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(image_url)
                return image_url
        return None
