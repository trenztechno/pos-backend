from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Vendor, VendorUser

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    business_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    gst_no = serializers.CharField(required=True, max_length=50)
    address = serializers.CharField(required=True)
    fssai_license = serializers.CharField(required=False, max_length=50, allow_blank=True, help_text="FSSAI License Number (optional during registration)")
    
    class Meta:
        model = Vendor
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'business_name', 'phone', 'gst_no', 'fssai_license', 'address']
    
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
    
    def validate_gst_no(self, value):
        if value and Vendor.objects.filter(gst_no=value).exists():
            raise serializers.ValidationError('GST number already registered.')
        return value
    
    def create(self, validated_data):
        password_confirm = validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        business_name = validated_data.pop('business_name')
        phone = validated_data.pop('phone')
        gst_no = validated_data.pop('gst_no')  # Required for new registrations
        fssai_license = validated_data.pop('fssai_license', None)  # Optional
        address = validated_data.pop('address')
        
        # Create user as inactive (requires admin approval)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False,  # Vendor must be approved by admin
        )
        
        # Create vendor profile (primary owner account)
        vendor = Vendor.objects.create(
            user=user,
            business_name=business_name,
            phone=phone,
            gst_no=gst_no,
            fssai_license=fssai_license,
            address=address,
            is_approved=False,  # Pending approval
        )

        # Link owner via VendorUser for multi-user support
        VendorUser.objects.create(
            vendor=vendor,
            user=user,
            is_owner=True,
            is_active=True,
            created_by=None,
        )

        return vendor

class LoginSerializer(serializers.Serializer):
    """
    Login serializer - validates username and password
    NOTE: Does NOT require GST number - vendors can login with or without GST
    GST number is only required for password reset, not for login
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid username or password. Please login.')
            
            # Determine if this user belongs to a vendor (owner or staff)
            vendor = Vendor.get_vendor_for_user(user)
            if vendor:
                # Vendor user (owner or staff)
                if not vendor.is_approved:
                    raise serializers.ValidationError(
                        'Your vendor account is pending approval. Please wait for admin approval.'
                    )
                if not user.is_active:
                    raise serializers.ValidationError(
                        'Your account is pending approval. Please wait for admin approval.'
                    )
            else:
                # Regular user (admin/salesrep) - just check if active
                if not user.is_active:
                    raise serializers.ValidationError('Your account is disabled.')
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password.')
        return attrs

class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for verifying username and GST number to initiate password reset"""
    username = serializers.CharField(required=True)
    gst_no = serializers.CharField(required=True, max_length=50)
    
    def validate(self, attrs):
        username = attrs.get('username')
        gst_no = attrs.get('gst_no')
        
        # Verify both username and GST number match.
        # Forgot-password is ONLY for the primary vendor owner account.
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('Username not found. Please check and try again.')

        # Must be primary vendor owner (has vendor_profile)
        try:
            vendor = user.vendor_profile
        except Vendor.DoesNotExist:
            raise serializers.ValidationError(
                'Username does not belong to a vendor owner account. Please contact your vendor admin.'
            )

        # Check if vendor has GST number
        if not vendor.gst_no:
            raise serializers.ValidationError(
                'Your vendor account does not have a GST number. Please contact admin to add GST number for password reset.'
            )

        # Check if GST number matches
        if vendor.gst_no != gst_no:
            raise serializers.ValidationError('Username and GST number do not match.')

        # Check if vendor is approved and active
        if not vendor.is_approved:
            raise serializers.ValidationError('Your vendor account is pending approval. Please contact admin.')
        if not vendor.user.is_active:
            raise serializers.ValidationError('Your account is inactive. Please contact admin.')

        return attrs

class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password after username and GST verification"""
    username = serializers.CharField(required=True)
    gst_no = serializers.CharField(required=True, max_length=50)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    new_password_confirm = serializers.CharField(required=True, write_only=True, min_length=6)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        
        username = attrs.get('username')
        gst_no = attrs.get('gst_no')
        
        # Verify both username and GST number match.
        # Reset-password is ONLY for the primary vendor owner account.
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('Username not found.')

        try:
            vendor = user.vendor_profile
        except Vendor.DoesNotExist:
            raise serializers.ValidationError(
                'Username does not belong to a vendor owner account. Please contact your vendor admin.'
            )

        # Check if vendor has GST number
        if not vendor.gst_no:
            raise serializers.ValidationError(
                'Your vendor account does not have a GST number. Please contact admin to add GST number for password reset.'
            )

        # Check if GST number matches
        if vendor.gst_no != gst_no:
            raise serializers.ValidationError('Username and GST number do not match.')

        # Check if vendor is approved and active
        if not vendor.is_approved:
            raise serializers.ValidationError('Your vendor account is pending approval.')
        if not vendor.user.is_active:
            raise serializers.ValidationError('Your account is inactive.')

        return attrs

class VendorProfileSerializer(serializers.ModelSerializer):
    """Serializer for vendor profile (GET/PATCH)"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'username', 'email',
            'business_name', 'phone', 'address',
            'gst_no', 'fssai_license',
            'logo', 'footer_note',
            'is_approved', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_approved', 'created_at', 'updated_at', 'gst_no']  # GST cannot be changed
    
    def validate_gst_no(self, value):
        """GST number cannot be changed via API (read-only)"""
        if self.instance and value != self.instance.gst_no:
            raise serializers.ValidationError('GST number cannot be changed. Please contact admin.')
        return value

