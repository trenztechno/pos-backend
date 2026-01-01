from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from auth_app.models import Vendor, SalesRep
from backend.audit_log import log_vendor_approval

@login_required
def vendor_list(request):
    """List all vendors with approval status"""
    # Check if user is a sales rep
    try:
        sales_rep = request.user.sales_rep_profile
        if not sales_rep.is_active:
            messages.error(request, 'Your sales rep account is not active.')
            return redirect('sales_rep:login')
    except SalesRep.DoesNotExist:
        # Check if user is staff (admin)
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Sales rep access required.')
            return redirect('sales_rep:login')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')  # all, pending, approved
    search_query = request.GET.get('search', '')
    
    # Get vendors
    vendors = Vendor.objects.all().select_related('user')
    
    # Apply filters
    if status_filter == 'pending':
        vendors = vendors.filter(is_approved=False, user__is_active=False)
    elif status_filter == 'approved':
        vendors = vendors.filter(is_approved=True, user__is_active=True)
    
    if search_query:
        vendors = vendors.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(business_name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Order by creation date (newest first)
    vendors = vendors.order_by('-created_at')
    
    context = {
        'vendors': vendors,
        'status_filter': status_filter,
        'search_query': search_query,
        'pending_count': Vendor.objects.filter(is_approved=False, user__is_active=False).count(),
        'approved_count': Vendor.objects.filter(is_approved=True, user__is_active=True).count(),
    }
    
    return render(request, 'sales_rep/vendor_list.html', context)

@login_required
@require_http_methods(["POST"])
def approve_vendor(request, vendor_id):
    """Approve a vendor"""
    # Check if user is a sales rep
    try:
        sales_rep = request.user.sales_rep_profile
        if not sales_rep.is_active:
            return JsonResponse({'error': 'Sales rep account not active'}, status=403)
    except SalesRep.DoesNotExist:
        if not request.user.is_staff:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    # Approve vendor
    vendor.is_approved = True
    vendor.user.is_active = True
    vendor.save()
    vendor.user.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Vendor {vendor.business_name or vendor.user.username} approved successfully'
        })
    
    messages.success(request, f'Vendor {vendor.business_name or vendor.user.username} approved successfully')
    return redirect('sales_rep:vendor_list')

@login_required
@require_http_methods(["POST"])
def reject_vendor(request, vendor_id):
    """Reject/Deactivate a vendor"""
    # Check if user is a sales rep
    try:
        sales_rep = request.user.sales_rep_profile
        if not sales_rep.is_active:
            return JsonResponse({'error': 'Sales rep account not active'}, status=403)
    except SalesRep.DoesNotExist:
        if not request.user.is_staff:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    # Reject vendor
    vendor.is_approved = False
    vendor.user.is_active = False
    vendor.save()
    vendor.user.save()
    
    # Log audit event
    log_vendor_approval(vendor, request.user, action='rejected')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Vendor {vendor.business_name or vendor.user.username} rejected/deactivated'
        })
    
    messages.success(request, f'Vendor {vendor.business_name or vendor.user.username} rejected/deactivated')
    return redirect('sales_rep:vendor_list')

@login_required
@require_http_methods(["POST"])
def bulk_approve(request):
    """Bulk approve multiple vendors"""
    # Check if user is a sales rep
    try:
        sales_rep = request.user.sales_rep_profile
        if not sales_rep.is_active:
            return JsonResponse({'error': 'Sales rep account not active'}, status=403)
    except SalesRep.DoesNotExist:
        if not request.user.is_staff:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    vendor_ids = request.POST.getlist('vendor_ids')
    if not vendor_ids:
        messages.error(request, 'No vendors selected')
        return redirect('sales_rep:vendor_list')
    
    vendors = Vendor.objects.filter(id__in=vendor_ids)
    count = 0
    for vendor in vendors:
        vendor.is_approved = True
        vendor.user.is_active = True
        vendor.save()
        vendor.user.save()
        count += 1
    
    messages.success(request, f'{count} vendor(s) approved successfully')
    return redirect('sales_rep:vendor_list')

def login_view(request):
    """Sales rep login"""
    if request.user.is_authenticated:
        return redirect('sales_rep:vendor_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            # Check if user is sales rep or staff
            try:
                sales_rep = user.sales_rep_profile
                if sales_rep.is_active:
                    login(request, user)
                    return redirect('sales_rep:vendor_list')
                else:
                    messages.error(request, 'Your sales rep account is not active.')
            except SalesRep.DoesNotExist:
                # Check if staff/admin
                if user.is_staff:
                    login(request, user)
                    return redirect('sales_rep:vendor_list')
                else:
                    messages.error(request, 'Access denied. Sales rep or admin access required.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'sales_rep/login.html')

@login_required
def vendor_detail(request, vendor_id):
    """View vendor details"""
    # Check if user is a sales rep
    try:
        sales_rep = request.user.sales_rep_profile
        if not sales_rep.is_active:
            messages.error(request, 'Your sales rep account is not active.')
            return redirect('sales_rep:login')
    except SalesRep.DoesNotExist:
        if not request.user.is_staff:
            messages.error(request, 'Access denied.')
            return redirect('sales_rep:login')
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    context = {
        'vendor': vendor,
    }
    
    return render(request, 'sales_rep/vendor_detail.html', context)
