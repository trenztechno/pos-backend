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
    gst_no = serializers.CharField(required=False, max_length=50, allow_blank=True, allow_null=True, help_text="GST Number (GSTIN) - Optional. Can be added later in profile settings.")
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
        # Convert empty string to None for consistency
        if value == '':
            value = None
        # Only validate uniqueness if GST number is provided
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
        gst_no = validated_data.pop('gst_no', None)  # Optional - can be None or empty string
        # Convert empty string to None for consistency
        if gst_no == '':
            gst_no = None
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
    """Serializer for verifying username and phone number to initiate password reset"""
    username = serializers.CharField(required=True)
    phone = serializers.CharField(required=True, max_length=20)
    
    def validate(self, attrs):
        username = attrs.get('username')
        phone = attrs.get('phone')
        
        # Verify both username and phone number match.
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

        # Check if vendor has phone number
        if not vendor.phone:
            raise serializers.ValidationError(
                'Your vendor account does not have a phone number. Please contact admin to add phone number for password reset.'
            )

        # Check if phone number matches (normalize by removing spaces, dashes, etc.)
        vendor_phone = vendor.phone.replace(' ', '').replace('-', '').replace('+', '')
        provided_phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        if vendor_phone != provided_phone:
            raise serializers.ValidationError('Username and phone number do not match.')

        # Check if vendor is approved and active
        if not vendor.is_approved:
            raise serializers.ValidationError('Your vendor account is pending approval. Please contact admin.')
        if not vendor.user.is_active:
            raise serializers.ValidationError('Your account is inactive. Please contact admin.')

        return attrs

class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password after username and phone verification"""
    username = serializers.CharField(required=True)
    phone = serializers.CharField(required=True, max_length=20)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    new_password_confirm = serializers.CharField(required=True, write_only=True, min_length=6)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        
        username = attrs.get('username')
        phone = attrs.get('phone')
        
        # Verify both username and phone number match.
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

        # Check if vendor has phone number
        if not vendor.phone:
            raise serializers.ValidationError(
                'Your vendor account does not have a phone number. Please contact admin to add phone number for password reset.'
            )

        # Check if phone number matches (normalize by removing spaces, dashes, etc.)
        vendor_phone = vendor.phone.replace(' ', '').replace('-', '').replace('+', '')
        provided_phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        if vendor_phone != provided_phone:
            raise serializers.ValidationError('Username and phone number do not match.')

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
    gst_no = serializers.CharField(required=False, max_length=50, allow_blank=True, allow_null=True, help_text="GST Number (GSTIN) - Optional. Can be set or updated via profile.")
    bill_prefix = serializers.CharField(required=False, allow_blank=True, max_length=50, help_text="Prefix for bill numbers (e.g., 'INV', 'BILL', 'REST')")
    bill_starting_number = serializers.IntegerField(required=False, min_value=1, help_text="Starting bill number (to account for existing bills before system migration)")
    last_bill_number = serializers.IntegerField(read_only=True, help_text="Last generated bill number (read-only, auto-incremented by server)")
    sac_code = serializers.CharField(required=False, max_length=20, allow_blank=True, allow_null=True, help_text="SAC (Service Accounting Code) for vendor-level GST. If set, all items use this SAC GST rate instead of their HSN codes.")
    sac_gst_percentage = serializers.DecimalField(required=False, max_digits=5, decimal_places=2, allow_null=True, min_value=0, max_value=100, help_text="GST percentage for SAC code (e.g., 5.00 for 5%). If SAC code is set but this is not set, default rate from mapping will be used.")
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'username', 'email',
            'business_name', 'phone', 'address',
            'gst_no', 'fssai_license',
            'logo', 'footer_note',
            'bill_prefix', 'bill_starting_number', 'last_bill_number',
            'sac_code', 'sac_gst_percentage',
            'is_approved', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_approved', 'created_at', 'updated_at', 'last_bill_number']  # last_bill_number cannot be changed
        # Note: gst_no is now editable (can be set/updated via profile update)
    
    def validate_gst_no(self, value):
        """Validate GST number if provided"""
        # Convert empty string to None for consistency
        if value == '':
            value = None
        # Only validate uniqueness if GST number is provided and different from current
        if value and self.instance:
            # Check if another vendor already has this GST number
            existing = Vendor.objects.filter(gst_no=value).exclude(id=self.instance.id).first()
            if existing:
                raise serializers.ValidationError('GST number already registered to another vendor.')
        elif value:
            # New GST number (during update)
            existing = Vendor.objects.filter(gst_no=value).first()
            if existing:
                raise serializers.ValidationError('GST number already registered to another vendor.')
        return value

