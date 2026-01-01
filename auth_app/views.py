from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import LoginSerializer, RegisterSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    POST /auth/register - Register new user (requires admin approval)
    Body: {
        "username": "user",
        "email": "user@example.com",
        "password": "password123",
        "password_confirm": "password123",
        "first_name": "John",
        "last_name": "Doe"
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
