from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
from .models import Item, Category
from .serializers import ItemSerializer, ItemListSerializer, CategorySerializer
from auth_app.models import Vendor
from backend.audit_log import log_item_change, log_category_change

class CategoryListView(APIView):
    """GET /items/categories - Get all categories for the vendor"""
    def get(self, request):
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if vendor is approved
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get only vendor's own categories
        categories = Category.objects.filter(vendor=vendor, is_active=True)
        
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    """POST /items/categories - Create new category"""
    def post(self, request):
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if vendor is approved
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save(vendor=vendor)
            return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryDetailView(APIView):
    """GET/PATCH/DELETE /items/categories/:id - Category operations"""
    def _check_vendor_approved(self, request):
        """Helper method to check vendor approval (works for owner + staff users)"""
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
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
        
        # Only allow viewing vendor's own categories
        try:
            category = Category.objects.get(id=id, vendor=vendor)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CategorySerializer(category)
        return Response(serializer.data)
    
    def patch(self, request, id):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        # Only allow updating vendor's own categories
        try:
            category = Category.objects.get(id=id, vendor=vendor)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        # Only allow deleting vendor's own categories
        try:
            category = Category.objects.get(id=id, vendor=vendor)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        
        category.delete()
        return Response({'message': 'Category deleted'}, status=status.HTTP_204_NO_CONTENT)

class ItemListView(APIView):
    """GET /items/ - Sync all items for the vendor (optionally filtered by category)"""
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # Support both JSON and file uploads
    
    def _check_vendor_approved(self, request):
        """Helper method to check vendor approval (works for owner + staff users)"""
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
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
        
        items = Item.objects.filter(vendor=vendor, is_active=True)
        
        # Filter by category if provided (items that belong to this category)
        category_id = request.query_params.get('category', None)
        if category_id:
            items = items.filter(categories__id=category_id).distinct()
        
        # Filter by search term if provided
        search = request.query_params.get('search', None)
        if search:
            items = items.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(sku__icontains=search) |
                Q(barcode__icontains=search)
            )
        
        serializer = ItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)
    
    """POST /items/ - Instant Add new item"""
    def post(self, request):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        serializer = ItemSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Validate categories - only allow vendor's own categories
            category_ids = request.data.get('categories', request.data.get('category_ids', request.data.get('category_ids_write', [])))
            validated_categories = None
            if category_ids:
                # Handle single category ID or list
                if not isinstance(category_ids, list):
                    category_ids = [category_ids]
                
                validated_categories = Category.objects.filter(
                    id__in=category_ids,
                    vendor=vendor  # Only vendor's own categories
                ).filter(is_active=True)
                
                if validated_categories.count() != len(category_ids):
                    return Response(
                        {'error': 'One or more categories not found or do not belong to vendor'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Save item (categories will be set via serializer if category_ids is in data)
            item = serializer.save(vendor=vendor)
            
            # Explicitly set categories if validated (ensures they're saved even if serializer didn't handle it)
            if validated_categories is not None:
                item.categories.set(validated_categories)
            
            # Log audit event
            log_item_change(item, vendor.user, action='created')
            
            return Response(ItemSerializer(item, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ItemDetailView(APIView):
    """GET/PATCH/DELETE /items/:id - Item operations"""
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # Support both JSON and file uploads
    
    def _check_vendor_approved(self, request):
        """Helper method to check vendor approval (works for owner + staff users)"""
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
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
            item = Item.objects.get(id=id, vendor=vendor)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ItemSerializer(item)
        return Response(serializer.data)
    
    def patch(self, request, id):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            item = Item.objects.get(id=id, vendor=vendor)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Last-Write-Wins: Update with timestamp
        item.last_updated = timezone.now()
        
        serializer = ItemSerializer(item, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            # Validate categories if being updated - only allow vendor's own categories
            validated_categories = None
            if 'categories' in request.data or 'category_ids' in request.data:
                category_ids = request.data.get('categories', request.data.get('category_ids', []))
                if category_ids:
                    # Handle single category ID or list
                    if not isinstance(category_ids, list):
                        category_ids = [category_ids]
                    
                    validated_categories = Category.objects.filter(
                        id__in=category_ids,
                        vendor=vendor  # Only vendor's own categories
                    ).filter(is_active=True)
                    
                    if validated_categories.count() != len(category_ids):
                        return Response(
                            {'error': 'One or more categories not found or do not belong to vendor'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            
            serializer.save()
            
            # Explicitly set categories if validated (ensures they're saved)
            if validated_categories is not None:
                item.categories.set(validated_categories)
            
            return Response(ItemSerializer(item, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        try:
            item = Item.objects.get(id=id, vendor=vendor)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        item.delete()
        return Response({'message': 'Item deleted'}, status=status.HTTP_204_NO_CONTENT)

class ItemStatusView(APIView):
    """PATCH /items/:id/status - Instant Stock Toggle (kept for backward compatibility)"""
    def patch(self, request, id):
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if vendor is approved
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            item = Item.objects.get(id=id, vendor=vendor)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Last-Write-Wins: Update with timestamp
        item.last_updated = timezone.now()
        
        # Toggle is_active or update stock_quantity if provided
        if 'is_active' in request.data:
            item.is_active = request.data['is_active']
        if 'stock_quantity' in request.data:
            item.stock_quantity = request.data['stock_quantity']
        
        item.save()
        serializer = ItemSerializer(item)
        return Response(serializer.data)

class CategorySyncView(APIView):
    """POST /items/categories/sync - Batch sync categories from mobile"""
    def _check_vendor_approved(self, request):
        """Helper method to check vendor approval (works for owner + staff users)"""
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return None, Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return None, Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return vendor, None
    
    def post(self, request):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        # Accept array of category operations or single operation
        operations = request.data if isinstance(request.data, list) else [request.data]
        
        synced_categories = []
        errors = []
        
        for op in operations:
            operation_type = op.get('operation', 'create')  # create, update, delete
            category_data = op.get('data', {})
            client_timestamp = op.get('timestamp', None)
            
            try:
                category_id = category_data.get('id') or op.get('id')
                
                if operation_type == 'delete':
                    # Delete category
                    if category_id:
                        try:
                            category = Category.objects.get(id=category_id, vendor=vendor)
                            category.delete()
                            synced_categories.append({
                                'id': str(category_id),
                                'operation': 'delete',
                                'status': 'success'
                            })
                        except Category.DoesNotExist:
                            errors.append({
                                'id': str(category_id),
                                'operation': 'delete',
                                'error': 'Category not found'
                            })
                    else:
                        errors.append({
                            'operation': 'delete',
                            'error': 'Category ID required for delete'
                        })
                
                elif operation_type == 'update' or operation_type == 'create':
                    # Create or update category
                    if category_id:
                        # Update existing
                        try:
                            category = Category.objects.get(id=category_id, vendor=vendor)
                            
                            # Last-Write-Wins: Check timestamp if provided
                            if client_timestamp:
                                try:
                                    # Parse ISO format timestamp
                                    if 'Z' in client_timestamp:
                                        client_time = datetime.fromisoformat(client_timestamp.replace('Z', '+00:00'))
                                    else:
                                        client_time = datetime.fromisoformat(client_timestamp)
                                    client_time = timezone.make_aware(client_time) if timezone.is_naive(client_time) else client_time
                                    
                                    if category.updated_at and category.updated_at > client_time:
                                        # Server version is newer, skip update
                                        synced_categories.append(CategorySerializer(category).data)
                                        continue
                                except (ValueError, AttributeError):
                                    # Invalid timestamp format, proceed with update
                                    pass
                            
                            # Update fields
                            serializer = CategorySerializer(category, data=category_data, partial=True)
                            if serializer.is_valid():
                                serializer.save()
                                synced_categories.append(serializer.data)
                            else:
                                errors.append({
                                    'id': str(category_id),
                                    'operation': operation_type,
                                    'error': serializer.errors
                                })
                        except Category.DoesNotExist:
                            # Create new with provided ID
                            category_data['id'] = category_id
                            serializer = CategorySerializer(data=category_data)
                            if serializer.is_valid():
                                category = serializer.save(vendor=vendor)
                                synced_categories.append(CategorySerializer(category).data)
                            else:
                                errors.append({
                                    'id': str(category_id),
                                    'operation': operation_type,
                                    'error': serializer.errors
                                })
                    else:
                        # Create new (generate ID)
                        serializer = CategorySerializer(data=category_data)
                        if serializer.is_valid():
                            category = serializer.save(vendor=vendor)
                            synced_categories.append(CategorySerializer(category).data)
                        else:
                            errors.append({
                                'operation': operation_type,
                                'error': serializer.errors
                            })
                
            except Exception as e:
                errors.append({
                    'operation': operation_type,
                    'error': str(e)
                })
        
        return Response({
            'synced': len(synced_categories),
            'categories': synced_categories,
            'errors': errors if errors else None
        }, status=status.HTTP_200_OK)

class ItemSyncView(APIView):
    """POST /items/sync - Batch sync items from mobile"""
    def _check_vendor_approved(self, request):
        """Helper method to check vendor approval (works for owner + staff users)"""
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return None, Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return None, Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return vendor, None
    
    def post(self, request):
        vendor, error_response = self._check_vendor_approved(request)
        if error_response:
            return error_response
        
        # Accept array of item operations or single operation
        operations = request.data if isinstance(request.data, list) else [request.data]
        
        synced_items = []
        errors = []
        
        for op in operations:
            operation_type = op.get('operation', 'create')  # create, update, delete
            item_data = op.get('data', {})
            client_timestamp = op.get('timestamp', None)
            
            try:
                item_id = item_data.get('id') or op.get('id')
                
                if operation_type == 'delete':
                    # Delete item
                    if item_id:
                        try:
                            item = Item.objects.get(id=item_id, vendor=vendor)
                            item.delete()
                            synced_items.append({
                                'id': str(item_id),
                                'operation': 'delete',
                                'status': 'success'
                            })
                        except Item.DoesNotExist:
                            errors.append({
                                'id': str(item_id),
                                'operation': 'delete',
                                'error': 'Item not found'
                            })
                    else:
                        errors.append({
                            'operation': 'delete',
                            'error': 'Item ID required for delete'
                        })
                
                elif operation_type == 'update' or operation_type == 'create':
                    # Create or update item
                    if item_id:
                        # Update existing
                        try:
                            item = Item.objects.get(id=item_id, vendor=vendor)
                            
                            # Last-Write-Wins: Check timestamp if provided
                            if client_timestamp:
                                try:
                                    # Parse ISO format timestamp
                                    if 'Z' in client_timestamp:
                                        client_time = datetime.fromisoformat(client_timestamp.replace('Z', '+00:00'))
                                    else:
                                        client_time = datetime.fromisoformat(client_timestamp)
                                    client_time = timezone.make_aware(client_time) if timezone.is_naive(client_time) else client_time
                                    
                                    if item.last_updated and item.last_updated > client_time:
                                        # Server version is newer, skip update
                                        synced_items.append(ItemSerializer(item, context={'request': request}).data)
                                        continue
                                except (ValueError, AttributeError):
                                    # Invalid timestamp format, proceed with update
                                    pass
                            
                            # Validate categories if provided - only vendor's own categories
                            category_ids = item_data.get('category_ids', item_data.get('categories', []))
                            validated_categories = None
                            if category_ids:
                                if not isinstance(category_ids, list):
                                    category_ids = [category_ids]
                                
                                validated_categories = Category.objects.filter(
                                    id__in=category_ids,
                                    vendor=vendor  # Only vendor's own categories
                                ).filter(is_active=True)
                                
                                if validated_categories.count() != len(category_ids):
                                    errors.append({
                                        'id': str(item_id),
                                        'operation': operation_type,
                                        'error': 'One or more categories not found or do not belong to vendor'
                                    })
                                    continue
                            
                            # Update fields
                            serializer = ItemSerializer(item, data=item_data, partial=True, context={'request': request})
                            if serializer.is_valid():
                                serializer.save()
                                if validated_categories is not None:
                                    item.categories.set(validated_categories)
                                synced_items.append(ItemSerializer(item, context={'request': request}).data)
                            else:
                                errors.append({
                                    'id': str(item_id),
                                    'operation': operation_type,
                                    'error': serializer.errors
                                })
                        except Item.DoesNotExist:
                            # Create new with provided ID
                            item_data['id'] = item_id
                            serializer = ItemSerializer(data=item_data)
                            if serializer.is_valid():
                                # Validate categories - only vendor's own categories
                                category_ids = item_data.get('category_ids', item_data.get('categories', []))
                                validated_categories = None
                                if category_ids:
                                    if not isinstance(category_ids, list):
                                        category_ids = [category_ids]
                                    
                                    validated_categories = Category.objects.filter(
                                        id__in=category_ids,
                                        vendor=vendor  # Only vendor's own categories
                                    ).filter(is_active=True)
                                    
                                    if validated_categories.count() != len(category_ids):
                                        errors.append({
                                            'id': str(item_id),
                                            'operation': operation_type,
                                            'error': 'One or more categories not found or do not belong to vendor'
                                        })
                                        continue
                                
                                item = serializer.save(vendor=vendor)
                                if validated_categories is not None:
                                    item.categories.set(validated_categories)
                                synced_items.append(ItemSerializer(item).data)
                            else:
                                errors.append({
                                    'id': str(item_id),
                                    'operation': operation_type,
                                    'error': serializer.errors
                                })
                    else:
                        # Create new (generate ID)
                        serializer = ItemSerializer(data=item_data)
                        if serializer.is_valid():
                            # Validate categories - only vendor's own categories
                            category_ids = item_data.get('category_ids', item_data.get('categories', []))
                            validated_categories = None
                            if category_ids:
                                if not isinstance(category_ids, list):
                                    category_ids = [category_ids]
                                
                                validated_categories = Category.objects.filter(
                                    id__in=category_ids,
                                    vendor=vendor  # Only vendor's own categories
                                ).filter(is_active=True)
                                
                                if validated_categories.count() != len(category_ids):
                                    errors.append({
                                        'operation': operation_type,
                                        'error': 'One or more categories not found or do not belong to vendor'
                                    })
                                    continue
                            
                            item = serializer.save(vendor=vendor)
                            if validated_categories is not None:
                                item.categories.set(validated_categories)
                            synced_items.append(ItemSerializer(item).data)
                        else:
                            errors.append({
                                'operation': operation_type,
                                'error': serializer.errors
                            })
                
            except Exception as e:
                errors.append({
                    'operation': operation_type,
                    'error': str(e)
                })
        
        return Response({
            'synced': len(synced_items),
            'items': synced_items,
            'errors': errors if errors else None
        }, status=status.HTTP_200_OK)
