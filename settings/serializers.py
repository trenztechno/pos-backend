from rest_framework import serializers
from .models import AppSettings

class AppSettingsSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    
    class Meta:
        model = AppSettings
        fields = ['id', 'vendor', 'vendor_name', 'device_id', 'settings_data', 'last_updated', 'created_at']
        read_only_fields = ['id', 'vendor', 'last_updated', 'created_at']

