from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from .models import InventoryItem, UnitType
from .serializers import InventoryItemSerializer, InventoryItemListSerializer, InventoryStockUpdateSerializer
from auth_app.models import Vendor
from backend.audit_log import log_item_change

class InventoryListView(APIView):
    """GET /inventory/ - List all inventory items for the vendor"""
    def _check_vendor_approved(self, request):
        """Helper method to check vendor approval"""
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            return None, Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return None, Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return vendor, None
    
    def get(self, request):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        # Get all inventory items for this vendor
        items = InventoryItem.objects.filter(vendor=vendor)
        
        # Filter by active status if provided
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            items = items.filter(is_active=is_active_bool)
        else:
            # Default: show only active items
            items = items.filter(is_active=True)
        
        # Filter by low stock if provided
        low_stock = request.query_params.get('low_stock', None)
        if low_stock and low_stock.lower() == 'true':
            items = [item for item in items if item.is_low_stock]
            # Convert back to queryset for serializer
            item_ids = [item.id for item in items]
            items = InventoryItem.objects.filter(id__in=item_ids)
        
        # Filter by search term if provided
        search = request.query_params.get('search', None)
        if search:
            items = items.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(sku__icontains=search) |
                Q(barcode__icontains=search) |
                Q(supplier_name__icontains=search)
            )
        
        # Filter by unit type if provided
        unit_type = request.query_params.get('unit_type', None)
        if unit_type:
            items = items.filter(unit_type=unit_type)
        
        # Use list serializer for listing
        serializer = InventoryItemListSerializer(items, many=True)
        return Response(serializer.data)
    
    """POST /inventory/ - Create new inventory item"""
    def post(self, request):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        serializer = InventoryItemSerializer(data=request.data)
        if serializer.is_valid():
            # Check if item with same name already exists for this vendor
            name = serializer.validated_data.get('name')
            if InventoryItem.objects.filter(vendor=vendor, name=name).exists():
                return Response(
                    {'error': f'Inventory item with name "{name}" already exists for your vendor account'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save item with vendor
            item = serializer.save(vendor=vendor)
            
            # Log audit event
            log_item_change(item, vendor.user, action='created', item_type='inventory')
            
            return Response(InventoryItemSerializer(item).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InventoryDetailView(APIView):
    """GET/PATCH/DELETE /inventory/:id - Inventory item operations"""
    def _check_vendor_approved(self, request):
        """Helper method to check vendor approval"""
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            return None, Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return None, Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return vendor, None
    
    def get(self, request, id):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            item = InventoryItem.objects.get(id=id, vendor=vendor)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = InventoryItemSerializer(item)
        return Response(serializer.data)
    
    def patch(self, request, id):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            item = InventoryItem.objects.get(id=id, vendor=vendor)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = InventoryItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            # Check if name is being changed and if new name already exists
            if 'name' in serializer.validated_data:
                new_name = serializer.validated_data['name']
                if new_name != item.name:
                    if InventoryItem.objects.filter(vendor=vendor, name=new_name).exists():
                        return Response(
                            {'error': f'Inventory item with name "{new_name}" already exists for your vendor account'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            
            serializer.save()
            
            # Log audit event
            log_item_change(item, vendor.user, action='updated', item_type='inventory')
            
            return Response(InventoryItemSerializer(item).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            item = InventoryItem.objects.get(id=id, vendor=vendor)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Log audit event before deletion
        log_item_change(item, vendor.user, action='deleted', item_type='inventory')
        
        item.delete()
        return Response({'message': 'Inventory item deleted'}, status=status.HTTP_204_NO_CONTENT)

class InventoryStockUpdateView(APIView):
    """PATCH /inventory/:id/stock - Update stock quantity"""
    def _check_vendor_approved(self, request):
        """Helper method to check vendor approval"""
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            return None, Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return None, Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return vendor, None
    
    def patch(self, request, id):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            item = InventoryItem.objects.get(id=id, vendor=vendor)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = InventoryStockUpdateSerializer(data=request.data)
        if serializer.is_valid():
            action = serializer.validated_data.get('action', 'set')
            new_quantity = serializer.validated_data.get('quantity')
            notes = serializer.validated_data.get('notes', '')
            
            # Update quantity based on action
            if action == 'set':
                item.quantity = new_quantity
            elif action == 'add':
                item.quantity += new_quantity
            elif action == 'subtract':
                item.quantity -= new_quantity
                if item.quantity < 0:
                    return Response(
                        {'error': 'Cannot subtract more than current quantity'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Update last_restocked_at if adding stock
            if action == 'add' and new_quantity > 0:
                item.last_restocked_at = timezone.now()
            
            item.save()
            
            # Log audit event
            log_item_change(
                item, 
                vendor.user, 
                action='stock_updated', 
                item_type='inventory',
                details=f"Action: {action}, Quantity: {new_quantity}",
                notes=notes if notes else None
            )
            
            return Response(InventoryItemSerializer(item).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InventoryUnitTypesView(APIView):
    """GET /inventory/unit-types - Get available unit types"""
    def get(self, request):
        # Return all available unit types
        unit_types = [
            {'value': choice[0], 'label': choice[1]}
            for choice in UnitType.choices
        ]
        return Response(unit_types)
