from rest_framework import serializers
from .models import SalesBackup

class SalesBackupSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    
    class Meta:
        model = SalesBackup
        fields = ['id', 'vendor', 'vendor_name', 'bill_data', 'device_id', 'synced_at', 'created_at']
        read_only_fields = ['id', 'vendor', 'synced_at', 'created_at']

