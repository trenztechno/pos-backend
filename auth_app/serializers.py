from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Vendor

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    business_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Vendor
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 
                  'business_name', 'phone', 'address']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists.')
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value
    
    def create(self, validated_data):
        password_confirm = validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        business_name = validated_data.pop('business_name', '')
        phone = validated_data.pop('phone', '')
        address = validated_data.pop('address', '')
        
        # Create user as inactive (requires admin approval)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False,  # Vendor must be approved by admin
        )
        
        # Create vendor profile
        vendor = Vendor.objects.create(
            user=user,
            business_name=business_name,
            phone=phone,
            address=address,
            is_approved=False  # Pending approval
        )
        
        return vendor

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid username or password. Please login.')
            
            # Check if this is a vendor (has vendor profile)
            try:
                vendor = user.vendor_profile
                # Vendor must be approved
                if not vendor.is_approved:
                    raise serializers.ValidationError('Your vendor account is pending approval. Please wait for admin approval.')
                # User must also be active
                if not user.is_active:
                    raise serializers.ValidationError('Your account is pending approval. Please wait for admin approval.')
            except Vendor.DoesNotExist:
                # Regular user (admin) - just check if active
                if not user.is_active:
                    raise serializers.ValidationError('Your account is disabled.')
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password.')
        return attrs

