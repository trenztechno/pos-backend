from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import SalesBackup
from .serializers import SalesBackupSerializer
from auth_app.models import Vendor

class SalesSyncView(APIView):
    """POST /backup/sync - Batch Sales Upload (Passive Receiver)"""
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
        
        # Accept array of bills or single bill
        bills = request.data if isinstance(request.data, list) else [request.data]
        
        created_bills = []
        for bill_data in bills:
            serializer = SalesBackupSerializer(data={
                'bill_data': bill_data.get('bill_data', bill_data),
                'device_id': bill_data.get('device_id', '')
            })
            if serializer.is_valid():
                # Save with vendor
                backup = serializer.save(vendor=vendor)
                created_bills.append(SalesBackupSerializer(backup).data)
            else:
                # Still save even if validation fails (passive receiver)
                backup = SalesBackup.objects.create(
                    vendor=vendor,
                    bill_data=bill_data.get('bill_data', bill_data),
                    device_id=bill_data.get('device_id', '')
                )
                created_bills.append(SalesBackupSerializer(backup).data)
        
        return Response({
            'synced': len(created_bills),
            'bills': created_bills
        }, status=status.HTTP_201_CREATED)
