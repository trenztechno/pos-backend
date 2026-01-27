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
from auth_app.models import Vendor

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
                
                # Extract bill header data
                invoice_number = bill_data.get('invoice_number') or bill_data.get('bill_id', str(uuid.uuid4()))
                
                # Check if bill already exists (prevent duplicates)
                existing_bill = Bill.objects.filter(
                    vendor=vendor,
                    invoice_number=invoice_number
                ).first()
                
                if existing_bill:
                    # Bill already exists, skip or update
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
