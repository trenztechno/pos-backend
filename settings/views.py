from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AppSettings
from .serializers import AppSettingsSerializer
from auth_app.models import Vendor

class SettingsPushView(APIView):
    """POST /settings/push - Config Backup"""
    def post(self, request):
        # Check vendor approval
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        device_id = request.data.get('device_id')
        settings_data = request.data.get('settings_data', request.data)
        
        if not device_id:
            return Response({'error': 'device_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update or create (Last-Write-Wins) - vendor-specific
        settings, created = AppSettings.objects.update_or_create(
            vendor=vendor,
            device_id=device_id,
            defaults={'settings_data': settings_data}
        )
        
        serializer = AppSettingsSerializer(settings)
        return Response(serializer.data, 
                       status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
