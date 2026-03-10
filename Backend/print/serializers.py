# serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db import transaction
from .models import *



# serializers.py - CORRECTED VERSION
from rest_framework import serializers
from django.db import transaction
from .models import User, UserProfile, ShopProfile

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile data."""
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'address', 'phone', 'email', 'college',
            'is_active', 'is_suspended', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShopProfileSerializer(serializers.ModelSerializer):
    """Serializer for shop profile data."""
    
    class Meta:
        model = ShopProfile
        fields = [
            'id', 'shop_name', 'address', 'phone', 'email',
            'gst_number', 'is_active', 'is_suspended',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user lists."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'role', 'role_display',
            'is_active', 'is_suspended', 'is_staff', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_staff']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer including profile data."""
    user_profile = UserProfileSerializer(read_only=True)
    shop_profile = ShopProfileSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'role', 'role_display', 'is_staff',
            'is_active', 'is_suspended', 'created_at', 'updated_at',
            'user_profile', 'shop_profile'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_staff']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users with profile data."""
    password = serializers.CharField(
        write_only=True, 
        min_length=8, 
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'}
    )
    
    # Conditional profile fields
    user_profile = UserProfileSerializer(required=False)
    shop_profile = ShopProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'password_confirm',
            'role', 'is_active', 'is_staff', 'user_profile', 'shop_profile'
        ]
        read_only_fields = ['id', 'is_staff']  # FIX: Corrected typo from 'is_satff'
    
    def validate(self, data):
        """Validate password match and role-specific profile data."""
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        role = data.get('role')
        
        # FIX: Only require profiles for user and shop roles, NOT for admin
        if role == User.ROLE_USER:
            if not data.get('user_profile'):
                raise serializers.ValidationError({
                    'user_profile': 'User profile data is required for regular users.'
                })
        
        elif role == User.ROLE_SHOP:
            if not data.get('shop_profile'):
                raise serializers.ValidationError({
                    'shop_profile': 'Shop profile data is required for shop owners.'
                })
        
        # Admin role doesn't need a profile - this is the fix!
        
        return data
    
    def create(self, validated_data):
        """Create user with associated profile in a transaction."""
        validated_data.pop('password_confirm')
        user_profile_data = validated_data.pop('user_profile', None)
        shop_profile_data = validated_data.pop('shop_profile', None)
        password = validated_data.pop('password')
        
        with transaction.atomic():
            # Create user (is_staff will be auto-set in save())
            user = User.objects.create(**validated_data)
            user.set_password(password)
            user.save()
            
            # Create appropriate profile based on role
            if user.role == User.ROLE_USER and user_profile_data:
                UserProfile.objects.create(user=user, **user_profile_data)
            elif user.role == User.ROLE_SHOP and shop_profile_data:
                ShopProfile.objects.create(user=user, **shop_profile_data)
            # Admin users don't get a profile
        
        return user


# Keep all other serializers (ChangePasswordSerializer, UserUpdateSerializer, etc.)
class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        """Validate password confirmation match."""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return data
    
    def validate_old_password(self, value):
        """Check if old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user and profile data."""
    user_profile = UserProfileSerializer(required=False)
    shop_profile = ShopProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'role', 'is_active', 'is_suspended',
            'user_profile', 'shop_profile'
        ]
        read_only_fields = ['id', 'role']  # Role cannot be changed after creation
    
    def update(self, instance, validated_data):
        """Update user and profile data in a transaction."""
        user_profile_data = validated_data.pop('user_profile', None)
        shop_profile_data = validated_data.pop('shop_profile', None)
        
        with transaction.atomic():
            # Update user fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # Update profiles
            if user_profile_data and hasattr(instance, 'user_profile'):
                for attr, value in user_profile_data.items():
                    setattr(instance.user_profile, attr, value)
                instance.user_profile.save()
            
            if shop_profile_data and hasattr(instance, 'shop_profile'):
                for attr, value in shop_profile_data.items():
                    setattr(instance.shop_profile, attr, value)
                instance.shop_profile.save()
        
        return instance





class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login with JWT token generation.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        """Validate credentials and return user."""
        username = data.get('username')
        password = data.get('password')
        
        try:
            user = User.objects.select_related(
                'user_profile', 'shop_profile'
            ).get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'error': 'Invalid username or password.'
            })
        
        if not user.check_password(password):
            raise serializers.ValidationError({
                'error': 'Invalid username or password.'
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                'error': 'Account is deactivated. Please contact support.'
            })
        
        if user.is_suspended:
            raise serializers.ValidationError({
                'error': 'Account is suspended. Please contact support.'
            })
        
        data['user'] = user
        return data


class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializer for refreshing JWT tokens.
    """
    refresh = serializers.CharField(required=True)
    
    def validate(self, data):
        """Validate and generate new tokens."""
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        try:
            refresh = RefreshToken(data['refresh'])
            data['access'] = str(refresh.access_token)
        except TokenError:
            raise serializers.ValidationError({
                'refresh': 'Invalid or expired refresh token.'
            })
        
        return data




class LogoutSerializer(serializers.Serializer):

    """
    Serializer for logout (blacklist refresh token).
    """
    refresh = serializers.CharField(required=True)
    
    def validate(self, data):
        """Blacklist the refresh token."""
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        try:
            token = RefreshToken(data['refresh'])
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError({
                'refresh': 'Invalid or expired token.'
            })
        
        return data
    




class OrderSerializer(serializers.ModelSerializer):
    """Main serializer for creating orders"""
    shop_profile = serializers.PrimaryKeyRelatedField(
        queryset=ShopProfile.objects.filter(is_active=True, is_suspended=False),
        source='selected_shop',
        required=True,
        allow_null=False
    )
    
    user_profile = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        required=False
    )
    
    class Meta:
        model = Order
        fields = [
            'id', 
            'order_name', 
            'file_path', 
            'pages_selected', 
            'color_or_black', 
            'landscape_or_portrait',
            'user_profile',
            'shop_profile',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """
        ✅ FIXED: Create order AND automatically create ShopOrder entries
        """
        # Get user_profile from context if not provided
        if 'user_profile' not in validated_data:
            request = self.context.get('request')
            if request and hasattr(request.user, 'userprofile'):
                validated_data['user_profile'] = request.user.userprofile
        
        selected_shop = validated_data['selected_shop']
        
        # Create the order
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            
            print(f"✅ Created Order #{order.id}")
            
            # ✅ AUTOMATICALLY CREATE ShopOrder ENTRY
            shop_order = ShopOrder.objects.create(
                order=order,
                shop_profile=selected_shop,
                status=ShopOrder.STATUS_PENDING
            )
            
            print(f"✅ Created ShopOrder #{shop_order.id} for shop {selected_shop.id}")
        
        return order



class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing (no file content)"""
    class Meta:
        model = Order
        fields = ['id', 'order_name', 'pages_selected', 'color_or_black', 
                  'landscape_or_portrait', 'created_at', 'user_profile']



class OrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with all info including file"""
    user_profile_name = serializers.CharField(source='user_profile.user.username', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'


# ============================================
# SHOP ORDER SERIALIZERS
# ============================================

class ShopOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing shop orders"""
    shop_name = serializers.CharField(source='shop_profile.shop_name', read_only=True)
    order_name = serializers.CharField(source='order.order_name', read_only=True)
    user_name = serializers.CharField(source='order.user_profile.user.username', read_only=True)
    
    class Meta:
        model = ShopOrder
        fields = [
            'id',
            'order_name',
            'shop_name',
            'user_name',
            'status',
            'quoted_price',
            'estimated_completion',
            'created_at',
        ]
        read_only_fields = fields


class ShopOrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for shop order with all information"""
    shop_name = serializers.CharField(source='shop_profile.shop_name', read_only=True)
    shop_email = serializers.EmailField(source='shop_profile.email', read_only=True)
    shop_phone = serializers.CharField(source='shop_profile.phone', read_only=True)
    shop_address = serializers.CharField(source='shop_profile.address', read_only=True)
    
    order_details = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopOrder
        fields = [
            'id',
            'status',
            'quoted_price',
            'estimated_completion',
            'order_details',
            'user_details',
            'shop_name',
            'shop_email',
            'shop_phone',
            'shop_address',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_order_details(self, obj):
        """Get complete order details"""
        order = obj.order
        return {
            'id': order.id,
            'order_name': order.order_name,
            'file_path': order.file_path.url if order.file_path else None,
            'pages_selected': order.pages_selected,
            'color_or_black': order.color_or_black,
            'landscape_or_portrait': order.landscape_or_portrait,
            'created_at': order.created_at,
        }

    def get_user_details(self, obj):
        """Get user contact details"""
        user_profile = obj.order.user_profile
        return {
            'user_id': user_profile.user.id,
            'username': user_profile.user.username,
            'email': user_profile.email,
            'phone': user_profile.phone,
            'college': user_profile.college,
        }


class ShopOrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating shop order (status, quote, etc.)"""
    
    class Meta:
        model = ShopOrder
        fields = [
            'status',
            'quoted_price',
            'estimated_completion',
        ]

    def validate_quoted_price(self, value):
        """Ensure quoted price is positive"""
        if value and value <= 0:
            raise serializers.ValidationError("Quoted price must be greater than 0.")
        return value



class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be positive.")
        return value


class PrdouctStoreVise(serializers.ModelSerializer):
    products = ProductSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "store_type",
            "is_open",
            "products",
        ]





# Add to your existing serializers.py

class ProductPaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    store_name   = serializers.CharField(source='order.store.name', read_only=True)

    class Meta:
        model  = ProductPayment
        fields = [
            'id', 'order_number', 'store_name',
            'razorpay_order_id', 'razorpay_payment_id',
            'amount', 'currency', 'status',
            'paid_at', 'created_at',
        ]
        read_only_fields = fields
