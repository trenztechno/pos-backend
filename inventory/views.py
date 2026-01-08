from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from .models import InventoryItem, UnitType
from .serializers import InventoryItemSerializer, InventoryItemListSerializer, StockUpdateSerializer
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
        """GET /inventory/ - Get all inventory items for the vendor"""
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        inventory_items = InventoryItem.objects.filter(vendor=vendor)
        
        # Filter by active status if provided
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            inventory_items = inventory_items.filter(is_active=is_active_bool)
        
        # Filter by low stock if provided
        low_stock = request.query_params.get('low_stock', None)
        if low_stock is not None and low_stock.lower() == 'true':
            inventory_items = [item for item in inventory_items if item.is_low_stock]
            # Convert back to queryset for serializer
            item_ids = [item.id for item in inventory_items]
            inventory_items = InventoryItem.objects.filter(id__in=item_ids)
        
        # Filter by search term if provided
        search = request.query_params.get('search', None)
        if search:
            inventory_items = inventory_items.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search) |
                Q(barcode__icontains=search) |
                Q(supplier__icontains=search) |
                Q(location__icontains=search)
            )
        
        # Filter by unit type if provided
        unit_type = request.query_params.get('unit_type', None)
        if unit_type:
            inventory_items = inventory_items.filter(unit_type=unit_type)
        
        serializer = InventoryItemListSerializer(inventory_items, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """POST /inventory/ - Create new inventory item"""
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        serializer = InventoryItemSerializer(data=request.data)
        if serializer.is_valid():
            # Check if item with same name already exists for this vendor
            name = serializer.validated_data.get('name')
            if InventoryItem.objects.filter(vendor=vendor, name=name).exists():
                return Response(
                    {'error': f'Inventory item with name "{name}" already exists for this vendor'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            inventory_item = serializer.save(vendor=vendor)
            
            # Log audit event
            log_item_change(inventory_item, vendor.user, action='created', item_type='inventory')
            
            return Response(
                InventoryItemSerializer(inventory_item).data,
                status=status.HTTP_201_CREATED
            )
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
        """GET /inventory/:id - Get specific inventory item"""
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            inventory_item = InventoryItem.objects.get(id=id, vendor=vendor)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = InventoryItemSerializer(inventory_item)
        return Response(serializer.data)
    
    def patch(self, request, id):
        """PATCH /inventory/:id - Update inventory item"""
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            inventory_item = InventoryItem.objects.get(id=id, vendor=vendor)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = InventoryItemSerializer(inventory_item, data=request.data, partial=True)
        if serializer.is_valid():
            # Check if name is being changed and conflicts with existing item
            if 'name' in serializer.validated_data:
                new_name = serializer.validated_data['name']
                if new_name != inventory_item.name:
                    if InventoryItem.objects.filter(vendor=vendor, name=new_name).exclude(id=id).exists():
                        return Response(
                            {'error': f'Inventory item with name "{new_name}" already exists for this vendor'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            
            serializer.save()
            
            # Log audit event
            log_item_change(inventory_item, vendor.user, action='updated', item_type='inventory')
            
            return Response(InventoryItemSerializer(inventory_item).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        """DELETE /inventory/:id - Delete inventory item"""
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            inventory_item = InventoryItem.objects.get(id=id, vendor=vendor)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Log audit event before deletion
        log_item_change(inventory_item, vendor.user, action='deleted', item_type='inventory')
        
        inventory_item.delete()
        return Response({'message': 'Inventory item deleted'}, status=status.HTTP_204_NO_CONTENT)

class StockUpdateView(APIView):
    """POST /inventory/:id/stock - Update stock quantity (add or subtract)"""
    
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
    
    def post(self, request, id):
        """POST /inventory/:id/stock - Update stock quantity"""
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            inventory_item = InventoryItem.objects.get(id=id, vendor=vendor)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StockUpdateSerializer(data=request.data)
        if serializer.is_valid():
            quantity_change = Decimal(str(serializer.validated_data['quantity']))
            notes = serializer.validated_data.get('notes', '')
            
            # Calculate new stock
            new_stock = inventory_item.current_stock + quantity_change
            
            # Prevent negative stock
            if new_stock < 0:
                return Response(
                    {'error': f'Insufficient stock. Current stock: {inventory_item.current_stock} {inventory_item.get_unit_type_display()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update stock
            old_stock = inventory_item.current_stock
            inventory_item.current_stock = new_stock
            
            # Update last_restocked if adding stock
            if quantity_change > 0:
                inventory_item.last_restocked = timezone.now()
            
            # Update notes if provided
            if notes:
                existing_notes = inventory_item.notes or ''
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                new_note = f"[{timestamp}] Stock update: {quantity_change:+} {inventory_item.get_unit_type_display()}. {notes}"
                inventory_item.notes = f"{existing_notes}\n{new_note}".strip() if existing_notes else new_note
            
            inventory_item.save()
            
            # Log audit event
            log_item_change(
                inventory_item,
                vendor.user,
                action='stock_updated',
                item_type='inventory',
                details=f'Stock changed from {old_stock} to {new_stock} {inventory_item.get_unit_type_display()}'
            )
            
            return Response({
                'message': 'Stock updated successfully',
                'inventory_item': InventoryItemSerializer(inventory_item).data,
                'old_stock': float(old_stock),
                'new_stock': float(new_stock),
                'change': float(quantity_change),
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnitTypesView(APIView):
    """GET /inventory/unit-types - Get all available unit types"""
    
    def get(self, request):
        """Return list of available unit types"""
        unit_types = [
            {'value': choice[0], 'label': choice[1]}
            for choice in UnitType.choices
        ]
        return Response(unit_types)
