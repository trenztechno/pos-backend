from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from auth_app.models import Vendor
from sales.models import Bill, BillItem
from items.models import Item


def get_vendor_from_request(request):
    """Helper to get vendor from request, return None if not vendor"""
    try:
        return request.user.vendor_profile
    except Vendor.DoesNotExist:
        return None


def parse_date_range(request):
    """Parse start_date and end_date from query params, default to today"""
    today = timezone.now().date()
    
    start_date_str = request.query_params.get('start_date')
    end_date_str = request.query_params.get('end_date')
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today
    else:
        start_date = today
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            end_date = today
    else:
        end_date = today
    
    # Ensure end_date >= start_date
    if end_date < start_date:
        end_date = start_date
    
    return start_date, end_date


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    GET /dashboard/stats - Overall dashboard statistics
    
    Query Parameters:
    - start_date: YYYY-MM-DD (optional, default: today)
    - end_date: YYYY-MM-DD (optional, default: today)
    
    Returns overall statistics for the vendor
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({
            'error': 'Vendor profile not found. This endpoint is only for vendors.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    start_date, end_date = parse_date_range(request)
    
    # Get bills in date range
    bills = Bill.objects.filter(
        vendor=vendor,
        bill_date__gte=start_date,
        bill_date__lte=end_date
    )
    
    # Calculate statistics
    total_bills = bills.count()
    gst_bills = bills.filter(billing_mode='gst').count()
    non_gst_bills = bills.filter(billing_mode='non_gst').count()
    
    total_revenue = bills.aggregate(
        total=Coalesce(Sum('total_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    total_tax_collected = bills.aggregate(
        total=Coalesce(Sum('total_tax'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    # Payment mode split
    payment_stats = bills.values('payment_mode').annotate(
        count=Count('id'),
        total=Coalesce(Sum('total_amount'), Decimal('0'), output_field=DecimalField())
    ).order_by('-total')
    
    payment_split = {
        'cash': {'count': 0, 'amount': Decimal('0')},
        'upi': {'count': 0, 'amount': Decimal('0')},
        'card': {'count': 0, 'amount': Decimal('0')},
        'credit': {'count': 0, 'amount': Decimal('0')},
        'other': {'count': 0, 'amount': Decimal('0')},
    }
    
    for stat in payment_stats:
        mode = stat['payment_mode']
        if mode in payment_split:
            payment_split[mode] = {
                'count': stat['count'],
                'amount': stat['total'] or Decimal('0')
            }
    
    return Response({
        'vendor_id': str(vendor.id),
        'vendor_name': vendor.business_name or vendor.user.username,
        'date_range': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'statistics': {
            'total_bills': total_bills,
            'gst_bills': gst_bills,
            'non_gst_bills': non_gst_bills,
            'total_revenue': str(total_revenue),
            'total_tax_collected': str(total_tax_collected),
            'payment_split': {
                k: {
                    'count': v['count'],
                    'amount': str(v['amount'])
                }
                for k, v in payment_split.items()
            }
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_sales(request):
    """
    GET /dashboard/sales - Sales analytics by billing mode
    
    Query Parameters:
    - start_date: YYYY-MM-DD (optional, default: today)
    - end_date: YYYY-MM-DD (optional, default: today)
    - billing_mode: 'gst' or 'non_gst' (optional, filter by billing mode)
    
    Returns sales analytics filtered by billing mode
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({
            'error': 'Vendor profile not found. This endpoint is only for vendors.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    start_date, end_date = parse_date_range(request)
    billing_mode = request.query_params.get('billing_mode')
    
    # Filter bills
    bills = Bill.objects.filter(
        vendor=vendor,
        bill_date__gte=start_date,
        bill_date__lte=end_date
    )
    
    if billing_mode in ['gst', 'non_gst']:
        bills = bills.filter(billing_mode=billing_mode)
    
    # Calculate sales metrics
    total_bills = bills.count()
    total_revenue = bills.aggregate(
        total=Coalesce(Sum('total_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    total_subtotal = bills.aggregate(
        total=Coalesce(Sum('subtotal'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    total_tax = bills.aggregate(
        total=Coalesce(Sum('total_tax'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    total_cgst = bills.aggregate(
        total=Coalesce(Sum('cgst_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    total_sgst = bills.aggregate(
        total=Coalesce(Sum('sgst_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    total_discount = bills.aggregate(
        total=Coalesce(Sum('discount_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    # Daily breakdown
    daily_breakdown = bills.values('bill_date').annotate(
        count=Count('id'),
        revenue=Coalesce(Sum('total_amount'), Decimal('0'), output_field=DecimalField()),
        tax=Coalesce(Sum('total_tax'), Decimal('0'), output_field=DecimalField())
    ).order_by('bill_date')
    
    return Response({
        'vendor_id': str(vendor.id),
        'date_range': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'filters': {
            'billing_mode': billing_mode or 'all'
        },
        'summary': {
            'total_bills': total_bills,
            'total_revenue': str(total_revenue),
            'total_subtotal': str(total_subtotal),
            'total_tax': str(total_tax),
            'total_cgst': str(total_cgst),
            'total_sgst': str(total_sgst),
            'total_discount': str(total_discount)
        },
        'daily_breakdown': [
            {
                'date': item['bill_date'].isoformat(),
                'bills_count': item['count'],
                'revenue': str(item['revenue']),
                'tax': str(item['tax'])
            }
            for item in daily_breakdown
        ]
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_items(request):
    """
    GET /dashboard/items - Item sales analytics (most/least sold dishes)
    
    Query Parameters:
    - start_date: YYYY-MM-DD (optional, default: today)
    - end_date: YYYY-MM-DD (optional, default: today)
    - sort: 'most_sold' or 'least_sold' (optional, default: 'most_sold')
    - limit: Integer (optional, default: 10) - Number of items to return
    
    Returns top/bottom selling items
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({
            'error': 'Vendor profile not found. This endpoint is only for vendors.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    start_date, end_date = parse_date_range(request)
    sort = request.query_params.get('sort', 'most_sold')
    limit = int(request.query_params.get('limit', 10))
    
    # Get bills in date range
    bills = Bill.objects.filter(
        vendor=vendor,
        bill_date__gte=start_date,
        bill_date__lte=end_date
    )
    
    # Get bill items and aggregate by item
    bill_items = BillItem.objects.filter(bill__in=bills)
    
    # Aggregate by item name (since item might be deleted)
    item_stats = bill_items.values('item_name').annotate(
        total_quantity=Coalesce(Sum('quantity'), Decimal('0'), output_field=DecimalField()),
        total_revenue=Coalesce(Sum('subtotal'), Decimal('0'), output_field=DecimalField()),
        bill_count=Count('bill', distinct=True)
    ).order_by('-total_quantity' if sort == 'most_sold' else 'total_quantity')[:limit]
    
    # Get item IDs for each item name (if linked)
    # Use a dictionary to track unique item_name -> item_id mappings
    item_name_to_id = {}
    # Get unique combinations of item_name and item_id
    unique_items = bill_items.select_related('item').values('item_name', 'item_id').distinct()
    for item_data in unique_items:
        item_name = item_data['item_name']
        item_id = item_data['item_id']
        if item_id and item_name not in item_name_to_id:
            item_name_to_id[item_name] = item_id
    
    # Format response
    items_list = []
    for stat in item_stats:
        item_name = stat['item_name']
        item_data = {
            'item_name': item_name,
            'total_quantity': str(stat['total_quantity']),
            'total_revenue': str(stat['total_revenue']),
            'bill_count': stat['bill_count'],
        }
        
        # Try to get item details if linked
        item_id = item_name_to_id.get(item_name)
        if item_id:
            try:
                item = Item.objects.get(id=item_id, vendor=vendor)
                item_data['item_id'] = str(item.id)
                categories = item.categories.all()[:1]
                item_data['category'] = [cat.name for cat in categories] if categories else []
                item_data['veg_nonveg'] = item.veg_nonveg
            except Item.DoesNotExist:
                pass
        
        items_list.append(item_data)
    
    return Response({
        'vendor_id': str(vendor.id),
        'date_range': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'sort': sort,
        'items': items_list
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_payments(request):
    """
    GET /dashboard/payments - Payment mode analytics (Cash/Card/UPI split)
    
    Query Parameters:
    - start_date: YYYY-MM-DD (optional, default: today)
    - end_date: YYYY-MM-DD (optional, default: today)
    
    Returns transaction split by payment mode
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({
            'error': 'Vendor profile not found. This endpoint is only for vendors.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    start_date, end_date = parse_date_range(request)
    
    # Get bills in date range
    bills = Bill.objects.filter(
        vendor=vendor,
        bill_date__gte=start_date,
        bill_date__lte=end_date
    )
    
    # Aggregate by payment mode
    payment_stats = bills.values('payment_mode').annotate(
        count=Count('id'),
        total_amount=Coalesce(Sum('total_amount'), Decimal('0'), output_field=DecimalField())
    ).order_by('-total_amount')
    
    # Calculate totals
    total_transactions = bills.count()
    total_revenue = bills.aggregate(
        total=Coalesce(Sum('total_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    # Format response
    payment_split = []
    for stat in payment_stats:
        amount = stat['total_amount'] or Decimal('0')
        percentage = (amount / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        payment_split.append({
            'payment_mode': stat['payment_mode'],
            'transaction_count': stat['count'],
            'total_amount': str(amount),
            'percentage': str(percentage.quantize(Decimal('0.01')))
        })
    
    return Response({
        'vendor_id': str(vendor.id),
        'date_range': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'summary': {
            'total_transactions': total_transactions,
            'total_revenue': str(total_revenue)
        },
        'payment_split': payment_split
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_tax(request):
    """
    GET /dashboard/tax - Tax collection analytics
    
    Query Parameters:
    - start_date: YYYY-MM-DD (optional, default: today)
    - end_date: YYYY-MM-DD (optional, default: today)
    
    Returns total tax collected (GST breakdown)
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({
            'error': 'Vendor profile not found. This endpoint is only for vendors.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    start_date, end_date = parse_date_range(request)
    
    # Get GST bills only
    bills = Bill.objects.filter(
        vendor=vendor,
        billing_mode='gst',
        bill_date__gte=start_date,
        bill_date__lte=end_date
    )
    
    # Calculate tax metrics
    total_tax = bills.aggregate(
        total=Coalesce(Sum('total_tax'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    total_cgst = bills.aggregate(
        total=Coalesce(Sum('cgst_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    total_sgst = bills.aggregate(
        total=Coalesce(Sum('sgst_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    total_igst = bills.aggregate(
        total=Coalesce(Sum('igst_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    gst_bills_count = bills.count()
    
    # Tax by GST percentage (from bill items)
    bill_items = BillItem.objects.filter(bill__in=bills)
    tax_by_percentage = bill_items.values('gst_percentage').annotate(
        item_count=Count('id'),
        tax_collected=Coalesce(Sum('item_gst_amount'), Decimal('0'), output_field=DecimalField())
    ).order_by('-gst_percentage')
    
    return Response({
        'vendor_id': str(vendor.id),
        'date_range': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'summary': {
            'gst_bills_count': gst_bills_count,
            'total_tax_collected': str(total_tax),
            'cgst_collected': str(total_cgst),
            'sgst_collected': str(total_sgst),
            'igst_collected': str(total_igst)
        },
        'tax_by_percentage': [
            {
                'gst_percentage': str(item['gst_percentage']),
                'item_count': item['item_count'],
                'tax_collected': str(item['tax_collected'])
            }
            for item in tax_by_percentage
        ]
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_profit(request):
    """
    GET /dashboard/profit - Net profit calculation (Admin/Vendor)
    
    Query Parameters:
    - start_date: YYYY-MM-DD (optional, default: today)
    - end_date: YYYY-MM-DD (optional, default: today)
    
    Returns net profit calculation
    Note: This is a basic calculation. For accurate profit, you need cost data (not currently stored)
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({
            'error': 'Vendor profile not found. This endpoint is only for vendors.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    start_date, end_date = parse_date_range(request)
    
    # Get bills in date range
    bills = Bill.objects.filter(
        vendor=vendor,
        bill_date__gte=start_date,
        bill_date__lte=end_date
    )
    
    # Calculate revenue
    total_revenue = bills.aggregate(
        total=Coalesce(Sum('total_amount'), Decimal('0'), output_field=DecimalField())
    )['total'] or Decimal('0')
    
    # Calculate costs (from bill items - using price as cost estimate)
    # Note: This is an approximation. Real profit needs actual cost data
    bill_items = BillItem.objects.filter(bill__in=bills)
    
    # Estimate cost (assuming 60% cost, 40% profit - this is configurable)
    # In real scenario, you'd have cost_price in Item model
    estimated_cost_percentage = Decimal('0.60')  # 60% cost
    estimated_cost = total_revenue * estimated_cost_percentage
    
    # Calculate profit
    gross_profit = total_revenue - estimated_cost
    
    # Tax is already paid, so net profit = gross profit
    net_profit = gross_profit
    
    return Response({
        'vendor_id': str(vendor.id),
        'date_range': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'profit_calculation': {
            'total_revenue': str(total_revenue),
            'estimated_cost': str(estimated_cost),
            'estimated_cost_percentage': str(estimated_cost_percentage * 100),
            'gross_profit': str(gross_profit),
            'net_profit': str(net_profit),
            'profit_margin_percentage': str((net_profit / total_revenue * 100).quantize(Decimal('0.01'))) if total_revenue > 0 else '0'
        },
        'note': 'Profit calculation is estimated based on 60% cost assumption. For accurate profit, actual cost data is required.'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_dues(request):
    """
    GET /dashboard/dues - Pending payments and dues
    
    Query Parameters:
    - start_date: YYYY-MM-DD (optional, default: today)
    - end_date: YYYY-MM-DD (optional, default: today)
    
    Returns pending payments and outstanding dues
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({
            'error': 'Vendor profile not found. This endpoint is only for vendors.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    start_date, end_date = parse_date_range(request)
    
    # Get bills in date range
    bills = Bill.objects.filter(
        vendor=vendor,
        bill_date__gte=start_date,
        bill_date__lte=end_date
    )
    
    # Calculate pending payments (credit bills or bills where amount_paid < total_amount)
    credit_bills = bills.filter(
        Q(payment_mode='credit') | Q(amount_paid__lt=F('total_amount'))
    )
    
    # Calculate total outstanding
    total_outstanding = Decimal('0')
    pending_bills = []
    
    for bill in credit_bills:
        amount_paid = bill.amount_paid or Decimal('0')
        outstanding = bill.total_amount - amount_paid
        total_outstanding += outstanding
        
        pending_bills.append({
            'bill_id': str(bill.id),
            'invoice_number': bill.invoice_number,
            'bill_date': bill.bill_date.isoformat(),
            'customer_name': bill.customer_name or 'N/A',
            'customer_phone': bill.customer_phone or 'N/A',
            'total_amount': str(bill.total_amount),
            'amount_paid': str(amount_paid),
            'outstanding_amount': str(outstanding),
            'payment_mode': bill.payment_mode,
            'days_pending': (timezone.now().date() - bill.bill_date).days
        })
    
    # Sort by outstanding amount (highest first)
    pending_bills.sort(key=lambda x: Decimal(x['outstanding_amount']), reverse=True)
    
    # Count by payment mode
    credit_count = bills.filter(payment_mode='credit').count()
    partial_payment_count = bills.filter(
        ~Q(payment_mode='credit'),
        amount_paid__lt=F('total_amount')
    ).count()
    
    return Response({
        'vendor_id': str(vendor.id),
        'date_range': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'summary': {
            'total_pending_bills': len(pending_bills),
            'total_outstanding_amount': str(total_outstanding),
            'credit_bills_count': credit_count,
            'partial_payment_bills_count': partial_payment_count
        },
        'pending_bills': pending_bills
    }, status=status.HTTP_200_OK)

