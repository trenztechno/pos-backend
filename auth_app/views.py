from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VendorProfileSerializer,
)
from .models import Vendor, VendorUser
from backend.s3_utils import generate_presigned_url


def get_vendor_from_request(request):
    """
    Helper to resolve the vendor for the current authenticated user.

    - Owner: via user.vendor_profile
    - Staff: via VendorUser relation
    """
    if not request.user.is_authenticated:
        return None
    return Vendor.get_vendor_for_user(request.user)


def is_vendor_owner(request, vendor=None):
    """
    Helper to check if the current user is the owner/admin of the vendor.
    """
    if vendor is None:
        vendor = get_vendor_from_request(request)
    if not vendor:
        return False
    return vendor.is_user_owner(request.user)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    POST /auth/register - Register new vendor (requires admin approval)
    Body: {
        "username": "vendor1",
        "email": "vendor@example.com",
        "password": "password123",
        "password_confirm": "password123",
        "business_name": "ABC Store",
        "phone": "+1234567890",
        "gst_no": "29ABCDE1234F1Z5",
        "address": "123 Main St, City"
    }
    Returns: {"message": "Registration successful. Please wait for admin approval."}
    """
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        vendor = serializer.save()
        return Response({
            'message': 'Registration successful. Your vendor account is pending approval. Please wait for admin approval.',
            'username': vendor.user.username,
            'business_name': vendor.business_name,
            'status': 'pending_approval'
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'error': 'Registration failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /auth/login - Login and get token
    Body: {"username": "user", "password": "pass"}
    Returns: {"token": "abc123...", "user_id": 1, "username": "user"}
    
    NOTE: Login does NOT require GST number. Vendors can login with just username and password.
    GST number is only required for password reset, not for login.
    This ensures backward compatibility with existing vendors.
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Get vendor profile if exists (for vendors)
        response_data = {
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'message': 'Login successful'
        }
        
        # Add vendor-specific data if user is a vendor (owner or staff)
        vendor = Vendor.get_vendor_for_user(user)
        if vendor:
            vendor_data = {
                'id': str(vendor.id),
                'business_name': vendor.business_name,
                'gst_no': vendor.gst_no,
                'fssai_license': vendor.fssai_license,
            }
            # Add logo URL if exists (works with both local and S3 storage)
            # Uses pre-signed URLs for S3 when enabled (more secure, no public bucket needed)
            if vendor.logo:
                # Check if using S3 with pre-signed URLs
                if settings.USE_S3 and getattr(settings, 'USE_S3_PRESIGNED_URLS', True):
                    presigned_url = generate_presigned_url(vendor.logo)
                    if presigned_url:
                        vendor_data['logo_url'] = presigned_url
                    else:
                        # Fallback to regular URL
                        logo_url = vendor.logo.url
                        if logo_url.startswith('http://') or logo_url.startswith('https://'):
                            vendor_data['logo_url'] = logo_url
                        else:
                            vendor_data['logo_url'] = request.build_absolute_uri(logo_url)
                else:
                    # S3 without pre-signed URLs, or local storage
                    logo_url = vendor.logo.url
                    if logo_url.startswith('http://') or logo_url.startswith('https://'):
                        vendor_data['logo_url'] = logo_url  # Already full URL (S3)
                    else:
                        vendor_data['logo_url'] = request.build_absolute_uri(logo_url)  # Local storage
            else:
                vendor_data['logo_url'] = None
            vendor_data['footer_note'] = vendor.footer_note
            response_data['vendor'] = vendor_data
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    # Check if error is about pending approval
    error_message = serializer.errors.get('non_field_errors', [])
    if error_message and 'pending approval' in str(error_message).lower():
        return Response({
            'error': 'Your account is pending approval. Please wait for admin approval.',
            'message': 'Your account has been created but is waiting for admin approval. You will be able to login once approved.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        'error': 'Invalid username or password. Please login.',
        'details': serializer.errors
    }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    """
    POST /auth/logout - Logout (delete token)
    Headers: Authorization: Token <token>
    """
    if request.user.is_authenticated:
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except:
            return Response({'message': 'Token already deleted'}, status=status.HTTP_200_OK)
    
    return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    POST /auth/forgot-password - Verify username and GST number to initiate password reset
    Body: {
        "username": "vendor1",
        "gst_no": "29ABCDE1234F1Z5"
    }
    Returns: {"message": "Username and GST number verified. You can now reset your password.", ...}
    """
    serializer = ForgotPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        username = serializer.validated_data['username']
        gst_no = serializer.validated_data['gst_no']
        user = User.objects.get(username=username)
        vendor = user.vendor_profile
        
        return Response({
            'message': 'Username and GST number verified. You can now reset your password.',
            'username': username,
            'gst_no': gst_no,
            'business_name': vendor.business_name
        }, status=status.HTTP_200_OK)
    
    return Response({
        'error': 'Username and GST number verification failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    POST /auth/reset-password - Reset password using username and GST number
    Body: {
        "username": "vendor1",
        "gst_no": "29ABCDE1234F1Z5",
        "new_password": "newpassword123",
        "new_password_confirm": "newpassword123"
    }
    Returns: {"message": "Password reset successful. You can now login with your new password."}
    """
    serializer = ResetPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        username = serializer.validated_data['username']
        gst_no = serializer.validated_data['gst_no']
        new_password = serializer.validated_data['new_password']
        
        user = User.objects.get(username=username)
        vendor = user.vendor_profile
        
        # Double-check GST matches (already validated in serializer, but extra safety)
        if vendor.gst_no != gst_no:
            return Response({
                'error': 'Username and GST number do not match.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Delete any existing tokens (force re-login)
        Token.objects.filter(user=user).delete()
        
        return Response({
            'message': 'Password reset successful. You can now login with your new password.',
            'username': user.username
        }, status=status.HTTP_200_OK)
    
    return Response({
        'error': 'Password reset failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    GET /auth/profile - Get vendor profile
    PATCH /auth/profile - Update vendor profile (logo, business details)
    
    Headers: Authorization: Token <token>
    
    PATCH Body (multipart/form-data for logo upload):
    {
        "business_name": "Updated Restaurant Name",
        "phone": "+1234567890",
        "address": "Updated Address",
        "fssai_license": "12345678901234",
        "footer_note": "Thank you!",
        "logo": <file>  // Optional image file
    }
    
    Returns: Vendor profile with logo_url (pre-signed URL if S3 enabled)
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response(
            {
                'error': 'Vendor profile not found. This endpoint is only for vendors.'
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    
    if request.method == 'GET':
        serializer = VendorProfileSerializer(vendor)
        data = serializer.data
        
        # Add logo_url with pre-signed URL if exists
        if vendor.logo:
            if settings.USE_S3 and getattr(settings, 'USE_S3_PRESIGNED_URLS', True):
                presigned_url = generate_presigned_url(vendor.logo)
                if presigned_url:
                    data['logo_url'] = presigned_url
                else:
                    logo_url = vendor.logo.url
                    if logo_url.startswith('http://') or logo_url.startswith('https://'):
                        data['logo_url'] = logo_url
                    else:
                        data['logo_url'] = request.build_absolute_uri(logo_url)
            else:
                logo_url = vendor.logo.url
                if logo_url.startswith('http://') or logo_url.startswith('https://'):
                    data['logo_url'] = logo_url
                else:
                    data['logo_url'] = request.build_absolute_uri(logo_url)
        else:
            data['logo_url'] = None
        
        return Response(data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = VendorProfileSerializer(vendor, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            # Get updated data with logo_url
            data = serializer.data
            if vendor.logo:
                if settings.USE_S3 and getattr(settings, 'USE_S3_PRESIGNED_URLS', True):
                    presigned_url = generate_presigned_url(vendor.logo)
                    if presigned_url:
                        data['logo_url'] = presigned_url
                    else:
                        logo_url = vendor.logo.url
                        if logo_url.startswith('http://') or logo_url.startswith('https://'):
                            data['logo_url'] = logo_url
                        else:
                            data['logo_url'] = request.build_absolute_uri(logo_url)
                else:
                    logo_url = vendor.logo.url
                    if logo_url.startswith('http://') or logo_url.startswith('https://'):
                        data['logo_url'] = logo_url
                    else:
                        data['logo_url'] = request.build_absolute_uri(logo_url)
            else:
                data['logo_url'] = None
            
            return Response({
                'message': 'Profile updated successfully',
                'vendor': data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Profile update failed',
            'details': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_staff_user(request):
    """
    POST /auth/vendor/users/create

    Vendor owner can create staff users (username + password) who can perform all
    billing actions but cannot manage other users or access Django admin.
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({'error': 'Vendor not found'}, status=status.HTTP_403_FORBIDDEN)

    if not is_vendor_owner(request, vendor):
        return Response(
            {'error': 'Only vendor owner can create staff users'},
            status=status.HTTP_403_FORBIDDEN,
        )

    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create Django user for staff (no admin access)
    user = User.objects.create_user(
        username=username,
        email=email or '',
        password=password,
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )

    vendor_user = VendorUser.objects.create(
        vendor=vendor,
        user=user,
        is_owner=False,
        is_active=True,
        created_by=request.user,
    )

    return Response(
        {
            'message': 'Staff user created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': 'staff',
                'created_at': vendor_user.created_at,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_vendor_users(request):
    """
    GET /auth/vendor/users

    List all users (owner + staff) for the current vendor.
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({'error': 'Vendor not found'}, status=status.HTTP_403_FORBIDDEN)

    vendor_users = vendor.vendor_users.filter(is_active=True).select_related('user')

    return Response(
        {
            'users': [
                {
                    'id': vu.user.id,
                    'username': vu.user.username,
                    'email': vu.user.email,
                    'role': 'owner' if vu.is_owner else 'staff',
                    'created_at': vu.created_at,
                    'created_by': vu.created_by.username if vu.created_by else None,
                }
                for vu in vendor_users
            ]
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_staff_password(request, user_id):
    """
    POST /auth/vendor/users/<user_id>/reset-password

    Vendor owner can reset password for a staff user.
    Staff users do NOT have public forgot-password flow.
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({'error': 'Vendor not found'}, status=status.HTTP_403_FORBIDDEN)

    if not is_vendor_owner(request, vendor):
        return Response(
            {'error': 'Only vendor owner can reset staff passwords'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        vendor_user = vendor.vendor_users.get(user_id=user_id, is_active=True)
    except VendorUser.DoesNotExist:
        return Response(
            {'error': 'User not found in this vendor'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if vendor_user.is_owner:
        return Response(
            {
                'error': 'Owner password must be reset via GST-based forgot-password flow.'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_password = request.data.get('new_password')
    if not new_password:
        return Response(
            {'error': 'new_password is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    vendor_user.user.set_password(new_password)
    vendor_user.user.save()

    # Invalidate tokens so staff must log in again with new password
    Token.objects.filter(user=vendor_user.user).delete()

    return Response(
        {'message': 'Staff user password reset successfully'},
        status=status.HTTP_200_OK,
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_staff_user(request, user_id):
    """
    DELETE /auth/vendor/users/<user_id>

    Vendor owner can deactivate a staff user (cannot remove owner).
    """
    vendor = get_vendor_from_request(request)
    if not vendor:
        return Response({'error': 'Vendor not found'}, status=status.HTTP_403_FORBIDDEN)

    if not is_vendor_owner(request, vendor):
        return Response(
            {'error': 'Only vendor owner can remove staff users'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        vendor_user = vendor.vendor_users.get(user_id=user_id, is_active=True)
    except VendorUser.DoesNotExist:
        return Response(
            {'error': 'User not found in this vendor'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if vendor_user.is_owner:
        return Response(
            {'error': 'Cannot remove owner account'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    vendor_user.is_active = False
    vendor_user.save()

    vendor_user.user.is_active = False
    vendor_user.user.save()

    # Invalidate tokens
    Token.objects.filter(user=vendor_user.user).delete()

    return Response(
        {'message': 'Staff user removed successfully'},
        status=status.HTTP_200_OK,
    )
