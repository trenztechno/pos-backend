from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import LoginSerializer, RegisterSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from .models import Vendor

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
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    
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
