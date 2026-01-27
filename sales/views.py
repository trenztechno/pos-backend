from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from .models import Bill, BillItem, SalesBackup
from .serializers import BillSerializer, BillListSerializer, BillItemSerializer, SalesBackupSerializer
from .utils import generate_bill_number
from auth_app.models import Vendor
from items.models import Item

class SalesSyncView(APIView):
    """
    GET /backup/sync - Download bills from server (for new devices)
    POST /backup/sync - Upload bills to server (from mobile app)
    """
    
    def get(self, request):
        """
        GET /backup/sync - Download bills for this vendor
        
        Query Parameters:
        - since: ISO timestamp (optional) - Only get bills synced after this time
        - limit: Integer (optional, default=1000) - Maximum number of bills to return
        - billing_mode: 'gst' or 'non_gst' (optional) - Filter by billing mode
        - start_date: YYYY-MM-DD (optional) - Filter by bill date
        - end_date: YYYY-MM-DD (optional) - Filter by bill date
        """
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get query parameters
        since = request.query_params.get('since')
        limit = int(request.query_params.get('limit', 1000))
        billing_mode = request.query_params.get('billing_mode')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Base queryset
        bills = Bill.objects.filter(vendor=vendor)
        
        # Apply filters
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                bills = bills.filter(synced_at__gte=since_dt)
            except ValueError:
                pass  # Invalid timestamp, ignore
        
        if billing_mode:
            bills = bills.filter(billing_mode=billing_mode)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                bills = bills.filter(bill_date__gte=start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                bills = bills.filter(bill_date__lte=end)
            except ValueError:
                pass
        
        # Order and limit
        bills = bills.order_by('-synced_at', '-created_at')[:limit]
        
        # Serialize
        serializer = BillSerializer(bills, many=True)
        
        return Response({
            'count': len(serializer.data),
            'bills': serializer.data,
            'vendor_id': str(vendor.id),
            'vendor_name': vendor.business_name
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        POST /backup/sync - Upload bills from mobile app
        
        Accepts:
        - Single bill object: { device_id, bill_data: {...} }
        - Array of bills: [{ device_id, bill_data: {...} }, ...]
        
        bill_data structure:
        {
            "invoice_number": "INV-2024-001",
            "bill_id": "uuid",
            "billing_mode": "gst" | "non_gst",
            "bill_number": "BN-001",
            "bill_date": "2024-01-22",
            "restaurant_name": "...",
            "address": "...",
            "gstin": "...",
            "fssai_license": "...",
            "logo_url": "...",
            "footer_note": "...",
            "items": [
                {
                    "id": "uuid",
                    "item_id": "uuid",
                    "name": "...",
                    "price": 100.00,
                    "mrp_price": 120.00,
                    "price_type": "exclusive",
                    "gst_percentage": 18.00,
                    "quantity": 2,
                    "subtotal": 200.00,
                    "item_gst": 36.00,
                    "veg_nonveg": "veg",
                    ...
                }
            ],
            "subtotal": 200.00,
            "cgst": 18.00,
            "sgst": 18.00,
            "igst": 0.00,
            "total_tax": 36.00,
            "total": 236.00,
            "payment_mode": "cash",
            "timestamp": "2024-01-22T10:00:00Z"
        }
        """
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Accept array of bills or single bill
        bills_data = request.data if isinstance(request.data, list) else [request.data]
        
        created_bills = []
        errors = []
        
        for bill_request in bills_data:
            try:
                device_id = bill_request.get('device_id', '')
                bill_data = bill_request.get('bill_data', bill_request)
                
                # Extract invoice number from bill_data (required for syncing)
                # POST /backup/sync only accepts bills with invoice_number (for syncing existing bills)
                # For creating new bills, use POST /bills/ which generates invoice_number automatically
                invoice_number = bill_data.get('invoice_number')
                
                if not invoice_number:
                    errors.append({
                        'bill': bill_data.get('bill_id', 'unknown'),
                        'error': 'invoice_number is required for syncing. Use POST /bills/ to create new bills.'
                    })
                    continue
                
                # Check if bill already exists (prevent duplicates)
                existing_bill = Bill.objects.filter(
                    vendor=vendor,
                    invoice_number=invoice_number
                ).first()
                
                if existing_bill:
                    # Bill already exists, skip (already synced)
                    created_bills.append(BillSerializer(existing_bill).data)
                    continue
                
                # Parse bill date
                bill_date_str = bill_data.get('bill_date')
                if bill_date_str:
                    try:
                        if isinstance(bill_date_str, str):
                            bill_date = datetime.fromisoformat(bill_date_str.split('T')[0]).date()
                        else:
                            bill_date = bill_date_str
                    except:
                        bill_date = timezone.now().date()
                else:
                    bill_date = timezone.now().date()
                
                # Parse created_at timestamp
                created_at_str = bill_data.get('timestamp') or bill_data.get('created_at')
                if created_at_str:
                    try:
                        if isinstance(created_at_str, str):
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        else:
                            created_at = created_at_str
                    except:
                        created_at = timezone.now()
                else:
                    created_at = timezone.now()
                
                # Create bill
                bill = Bill.objects.create(
                    vendor=vendor,
                    device_id=device_id,
                    invoice_number=invoice_number,
                    bill_number=bill_data.get('bill_number', ''),
                    bill_date=bill_date,
                    restaurant_name=bill_data.get('restaurant_name') or vendor.business_name,
                    address=bill_data.get('address') or vendor.address,
                    gstin=bill_data.get('gstin') or vendor.gst_no,
                    fssai_license=bill_data.get('fssai_license') or vendor.fssai_license,
                    logo_url=bill_data.get('logo_url'),
                    footer_note=bill_data.get('footer_note') or vendor.footer_note,
                    customer_name=bill_data.get('customer_name'),
                    customer_phone=bill_data.get('customer_phone'),
                    customer_email=bill_data.get('customer_email'),
                    customer_address=bill_data.get('customer_address'),
                    billing_mode=bill_data.get('billing_mode', 'gst'),
                    subtotal=Decimal(str(bill_data.get('subtotal', 0))),
                    total_amount=Decimal(str(bill_data.get('total', bill_data.get('total_amount', 0)))),
                    total_tax=Decimal(str(bill_data.get('total_tax', 0))),
                    cgst_amount=Decimal(str(bill_data.get('cgst', 0))),
                    sgst_amount=Decimal(str(bill_data.get('sgst', 0))),
                    igst_amount=Decimal(str(bill_data.get('igst', 0))),
                    payment_mode=bill_data.get('payment_mode', 'cash'),
                    payment_reference=bill_data.get('payment_reference'),
                    amount_paid=Decimal(str(bill_data.get('amount_paid', 0))) if bill_data.get('amount_paid') else None,
                    change_amount=Decimal(str(bill_data.get('change_amount', 0))),
                    discount_amount=Decimal(str(bill_data.get('discount_amount', 0))),
                    discount_percentage=Decimal(str(bill_data.get('discount_percentage', 0))),
                    notes=bill_data.get('notes'),
                    table_number=bill_data.get('table_number'),
                    waiter_name=bill_data.get('waiter_name'),
                    created_at=created_at
                )
                
                # Create bill items
                items_data = bill_data.get('items', [])
                for item_data in items_data:
                    # Try to link to master Item if item_id provided
                    item_id = item_data.get('item_id') or item_data.get('id')
                    item = None
                    if item_id:
                        try:
                            item = Item.objects.get(id=item_id, vendor=vendor)
                        except Item.DoesNotExist:
                            pass
                    
                    BillItem.objects.create(
                        bill=bill,
                        item=item,
                        original_item_id=item_id,
                        item_name=item_data.get('name', 'Unknown Item'),
                        item_description=item_data.get('description'),
                        price=Decimal(str(item_data.get('price', 0))),
                        mrp_price=Decimal(str(item_data.get('mrp_price', item_data.get('price', 0)))),
                        price_type=item_data.get('price_type', 'exclusive'),
                        quantity=Decimal(str(item_data.get('quantity', 1))),
                        subtotal=Decimal(str(item_data.get('subtotal', item_data.get('quantity', 1) * item_data.get('price', 0)))),
                        gst_percentage=Decimal(str(item_data.get('gst_percentage', 0))),
                        item_gst_amount=Decimal(str(item_data.get('item_gst', 0))),
                        veg_nonveg=item_data.get('veg_nonveg'),
                        additional_discount=Decimal(str(item_data.get('additional_discount', 0))),
                        discount_amount=Decimal(str(item_data.get('discount_amount', 0))),
                        unit=item_data.get('unit'),
                        batch_number=item_data.get('batch_number'),
                        expiry_date=datetime.fromisoformat(item_data.get('expiry_date')).date() if item_data.get('expiry_date') else None,
                    )
                
                created_bills.append(BillSerializer(bill).data)
                
            except Exception as e:
                errors.append({
                    'bill_data': bill_request.get('bill_data', {}).get('invoice_number', 'Unknown'),
                    'error': str(e)
                })
        
        response_data = {
            'synced': len(created_bills),
            'bills': created_bills
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class BillListView(APIView):
    """
    GET /bills/ - List all bills for the vendor
    POST /bills/ - Create a new bill
    """
    
    def get(self, request):
        """
        GET /bills/ - List all bills for this vendor
        
        Query Parameters:
        - billing_mode: 'gst' or 'non_gst' (optional) - Filter by billing mode
        - start_date: YYYY-MM-DD (optional) - Filter by bill date
        - end_date: YYYY-MM-DD (optional) - Filter by bill date
        - payment_mode: 'cash', 'upi', 'card', 'credit', 'other' (optional) - Filter by payment mode
        - limit: Integer (optional, default=100) - Maximum number of bills to return
        - offset: Integer (optional, default=0) - Number of bills to skip (for pagination)
        """
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get query parameters
        billing_mode = request.query_params.get('billing_mode')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        payment_mode = request.query_params.get('payment_mode')
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        
        # Base queryset
        bills = Bill.objects.filter(vendor=vendor)
        
        # Apply filters
        if billing_mode:
            bills = bills.filter(billing_mode=billing_mode)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                bills = bills.filter(bill_date__gte=start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                bills = bills.filter(bill_date__lte=end)
            except ValueError:
                pass
        
        if payment_mode:
            bills = bills.filter(payment_mode=payment_mode)
        
        # Get total count before pagination
        total_count = bills.count()
        
        # Order and paginate
        bills = bills.order_by('-created_at', '-bill_date')[offset:offset + limit]
        
        # Serialize
        serializer = BillListSerializer(bills, many=True)
        
        return Response({
            'count': len(serializer.data),
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'bills': serializer.data
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        POST /bills/ - Create a new bill
        
        Request Body:
        {
            "bill_date": "2024-01-22",  // Optional, defaults to today
            "billing_mode": "gst" | "non_gst",  // Required
            "items_data": [  // Required - array of items
                {
                    "item_id": "uuid",  // Optional - link to master Item
                    "item_name": "Pizza",  // Required
                    "price": 100.00,  // Required
                    "mrp_price": 120.00,  // Required
                    "price_type": "exclusive",  // Optional, default: "exclusive"
                    "gst_percentage": 18.00,  // Optional, default: 0
                    "quantity": 2,  // Required
                    "veg_nonveg": "veg",  // Optional
                    "additional_discount": 0.00,  // Optional
                    ...
                }
            ],
            "subtotal": 200.00,  // Optional - will be calculated if not provided
            "cgst": 18.00,  // Optional - for GST bills
            "sgst": 18.00,  // Optional - for GST bills
            "igst": 0.00,  // Optional - for GST bills
            "total_tax": 36.00,  // Optional - for GST bills
            "total": 236.00,  // Optional - will be calculated if not provided
            "payment_mode": "cash",  // Required
            "amount_paid": 236.00,  // Optional
            "change_amount": 0.00,  // Optional
            "customer_name": "...",  // Optional
            "customer_phone": "...",  // Optional
            "notes": "...",  // Optional
            ...
        }
        """
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get device_id from request (optional)
        device_id = request.data.get('device_id', '')
        
        # Server always generates invoice number (client cannot provide it)
        # This ensures sequential numbering across all devices
        invoice_number, bill_number = generate_bill_number(vendor)
        
        # Parse bill date
        bill_date_str = request.data.get('bill_date')
        if bill_date_str:
            try:
                if isinstance(bill_date_str, str):
                    bill_date = datetime.strptime(bill_date_str, '%Y-%m-%d').date()
                else:
                    bill_date = bill_date_str
            except:
                bill_date = timezone.now().date()
        else:
            bill_date = timezone.now().date()
        
        # Prepare bill data
        bill_data = {
            'vendor': vendor,
            'device_id': device_id,
            'invoice_number': invoice_number,
            'bill_number': bill_number or '',
            'bill_date': bill_date,
            'restaurant_name': request.data.get('restaurant_name') or vendor.business_name,
            'address': request.data.get('address') or vendor.address,
            'gstin': request.data.get('gstin') or vendor.gst_no,
            'fssai_license': request.data.get('fssai_license') or vendor.fssai_license,
            'logo_url': request.data.get('logo_url'),
            'footer_note': request.data.get('footer_note') or vendor.footer_note,
            'customer_name': request.data.get('customer_name'),
            'customer_phone': request.data.get('customer_phone'),
            'customer_email': request.data.get('customer_email'),
            'customer_address': request.data.get('customer_address'),
            'billing_mode': request.data.get('billing_mode', 'gst'),
            'subtotal': Decimal(str(request.data.get('subtotal', 0))),
            'total_amount': Decimal(str(request.data.get('total', request.data.get('total_amount', 0)))),
            'total_tax': Decimal(str(request.data.get('total_tax', 0))),
            'cgst_amount': Decimal(str(request.data.get('cgst', 0))),
            'sgst_amount': Decimal(str(request.data.get('sgst', 0))),
            'igst_amount': Decimal(str(request.data.get('igst', 0))),
            'payment_mode': request.data.get('payment_mode', 'cash'),
            'payment_reference': request.data.get('payment_reference'),
            'amount_paid': Decimal(str(request.data.get('amount_paid', 0))) if request.data.get('amount_paid') else None,
            'change_amount': Decimal(str(request.data.get('change_amount', 0))),
            'discount_amount': Decimal(str(request.data.get('discount_amount', 0))),
            'discount_percentage': Decimal(str(request.data.get('discount_percentage', 0))),
            'notes': request.data.get('notes'),
            'table_number': request.data.get('table_number'),
            'waiter_name': request.data.get('waiter_name'),
        }
        
        # Use serializer to create bill with items
        serializer = BillSerializer(data={**bill_data, 'items_data': request.data.get('items_data', [])})
        
        if serializer.is_valid():
            bill = serializer.save()
            return Response(BillSerializer(bill).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BillDetailView(APIView):
    """
    GET /bills/<id>/ - Get bill details
    PATCH /bills/<id>/ - Update bill (including items)
    DELETE /bills/<id>/ - Delete bill
    """
    
    def get(self, request, bill_id):
        """GET /bills/<id>/ - Get bill details"""
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            bill = Bill.objects.get(id=bill_id, vendor=vendor)
        except Bill.DoesNotExist:
            return Response({'error': 'Bill not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BillSerializer(bill)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, bill_id):
        """
        PATCH /bills/<id>/ - Update bill
        
        Can update:
        - Bill header fields (customer info, payment mode, etc.)
        - Items (by providing items_data array - will replace all items)
        - Financial fields (subtotal, tax, total, etc.)
        
        Request Body (all fields optional):
        {
            "items_data": [  // If provided, replaces all existing items
                {
                    "item_id": "uuid",
                    "item_name": "Updated Pizza",
                    "price": 150.00,
                    "mrp_price": 180.00,
                    "quantity": 3,
                    ...
                }
            ],
            "payment_mode": "upi",
            "amount_paid": 500.00,
            "customer_name": "Updated Customer",
            "subtotal": 450.00,
            "total": 531.00,
            ...
        }
        """
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            bill = Bill.objects.get(id=bill_id, vendor=vendor)
        except Bill.DoesNotExist:
            return Response({'error': 'Bill not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare update data
        update_data = {}
        
        # Update bill fields if provided
        if 'bill_date' in request.data:
            bill_date_str = request.data.get('bill_date')
            try:
                if isinstance(bill_date_str, str):
                    update_data['bill_date'] = datetime.strptime(bill_date_str, '%Y-%m-%d').date()
                else:
                    update_data['bill_date'] = bill_date_str
            except:
                pass
        
        if 'billing_mode' in request.data:
            update_data['billing_mode'] = request.data.get('billing_mode')
        
        if 'subtotal' in request.data:
            update_data['subtotal'] = Decimal(str(request.data.get('subtotal')))
        
        if 'total_amount' in request.data or 'total' in request.data:
            update_data['total_amount'] = Decimal(str(request.data.get('total', request.data.get('total_amount'))))
        
        if 'total_tax' in request.data:
            update_data['total_tax'] = Decimal(str(request.data.get('total_tax')))
        
        if 'cgst_amount' in request.data or 'cgst' in request.data:
            update_data['cgst_amount'] = Decimal(str(request.data.get('cgst', request.data.get('cgst_amount'))))
        
        if 'sgst_amount' in request.data or 'sgst' in request.data:
            update_data['sgst_amount'] = Decimal(str(request.data.get('sgst', request.data.get('sgst_amount'))))
        
        if 'igst_amount' in request.data or 'igst' in request.data:
            update_data['igst_amount'] = Decimal(str(request.data.get('igst', request.data.get('igst_amount'))))
        
        if 'payment_mode' in request.data:
            update_data['payment_mode'] = request.data.get('payment_mode')
        
        if 'payment_reference' in request.data:
            update_data['payment_reference'] = request.data.get('payment_reference')
        
        if 'amount_paid' in request.data:
            amount_paid = request.data.get('amount_paid')
            update_data['amount_paid'] = Decimal(str(amount_paid)) if amount_paid else None
        
        if 'change_amount' in request.data:
            update_data['change_amount'] = Decimal(str(request.data.get('change_amount')))
        
        if 'discount_amount' in request.data:
            update_data['discount_amount'] = Decimal(str(request.data.get('discount_amount')))
        
        if 'discount_percentage' in request.data:
            update_data['discount_percentage'] = Decimal(str(request.data.get('discount_percentage')))
        
        # Update other fields
        for field in ['restaurant_name', 'address', 'gstin', 'fssai_license', 'logo_url', 'footer_note',
                     'customer_name', 'customer_phone', 'customer_email', 'customer_address',
                     'notes', 'table_number', 'waiter_name']:
            if field in request.data:
                update_data[field] = request.data.get(field)
        
        # Use serializer to update
        serializer = BillSerializer(bill, data={**update_data, 'items_data': request.data.get('items_data')}, partial=True)
        
        if serializer.is_valid():
            updated_bill = serializer.save()
            return Response(BillSerializer(updated_bill).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, bill_id):
        """DELETE /bills/<id>/ - Delete bill"""
        vendor = Vendor.get_vendor_for_user(request.user)
        if not vendor:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)
        
        if not vendor.is_approved or not request.user.is_active:
            return Response({
                'error': 'Your vendor account is pending approval. Please wait for admin approval.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            bill = Bill.objects.get(id=bill_id, vendor=vendor)
        except Bill.DoesNotExist:
            return Response({'error': 'Bill not found'}, status=status.HTTP_404_NOT_FOUND)
        
        bill.delete()
        return Response({'message': 'Bill deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
