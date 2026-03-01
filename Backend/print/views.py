from django.shortcuts import render
from rest_framework.views import APIView
# Create your views here.
# views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny,IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from .models import User, UserProfile, ShopProfile
from .serializers import *
from .permissions import IsOwnerOrAdmin, IsAdminOrReadOnly
from django.utils import timezone
from  .utils import get_tokens_for_user
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
class LoginAPIView(APIView):
    """
    API endpoint for user login with JWT token generation.
    
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        """Authenticate user and return JWT tokens."""
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Get user profile data
            user_data = UserDetailSerializer(user).data
            
            return Response({
                'message': 'Login successful.',
                'access_token': tokens['access'],
                'refresh_token': tokens['refresh'],
                'user': user_data
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class RefreshTokenAPIView(APIView):
    """
    API endpoint to refresh access token.
    
    POST /api/auth/refresh/
    """
    permission_classes = [AllowAny]
    serializer_class = RefreshTokenSerializer
    
    def post(self, request):
        """Generate new access token from refresh token."""
        serializer = RefreshTokenSerializer(data=request.data)
        
        if serializer.is_valid():
            return Response({
                'access_token': serializer.validated_data['access']
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutAPIView(APIView):
    """
    API endpoint for user logout (blacklist refresh token).
    
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    
    def post(self, request):
        """Blacklist the refresh token to logout user."""
        serializer = LogoutSerializer(data=request.data)
        
        if serializer.is_valid():
            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

 
    # ViewSet for user management with full CRUD operations.
    
    # Endpoints:
    # - GET    /api/users/                    - List all users (paginated, filterable)
    # - POST   /api/users/                    - Register a new user
    # - GET    /api/users/{id}/               - Get user details by ID
    # - PUT    /api/users/{id}/               - Update user information (full)
    # - PATCH  /api/users/{id}/               - Partially update user
    # - DELETE /api/users/{id}/               - Deactivate user (soft delete)
    # - GET    /api/users/me/                 - Get current authenticated user
    # - POST   /api/users/change-password/    - Change password
    # - POST   /api/users/{id}/suspend/       - Suspend a user account (admin only)
    # - POST   /api/users/{id}/activate/      - Activate a suspended user (admin only)
    # - GET    /api/users/statistics/         - Get user statistics (admin only)
    # - GET    /api/users/{id}/orders/        - Get user's orders
    

class UserViewSet(viewsets.ModelViewSet):   




    """
    ViewSet for user management with JWT authentication.
    """
    queryset = User.objects.all().select_related(
        'user_profile', 'shop_profile'
    ).order_by('-created_at')
    
    # Don't set default permission_classes here, handle in get_permissions()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active', 'is_suspended']
    search_fields = ['username', 'user_profile__email', 'shop_profile__shop_name']
    ordering_fields = ['created_at', 'username', 'last_login']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        else:
            return UserDetailSerializer
    
    def get_permissions(self):
        """
        Set permissions based on action.
        """
        if self.action == 'create':
            # Public registration - anyone can create account
            return [AllowAny()]
        
        elif self.action == 'list':
            # Only authenticated users can list users
            # But they'll only see themselves (unless admin)
            return [IsAuthenticated()]
        
        elif self.action == 'retrieve':
            # Users can view their own profile, admins can view anyone
            return [IsAuthenticated()]
        
        elif self.action in ['update', 'partial_update']:
            # Users can update their own profile, admins can update anyone
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        
        elif self.action == 'destroy':
            # Only the user themselves or admin can delete
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        
        elif self.action in ['me', 'change_password', 'user_orders']:
            # Authenticated users only
            return [IsAuthenticated()]
        
        elif self.action in ['suspend', 'activate', 'statistics', 'search_users']:
            # Admin-only actions
            return [IsAuthenticated(), IsAdminUser()]
        
        # Default: require authentication
        return [IsAuthenticated()]
    
    def get_queryset(self):
   
        queryset = super().get_queryset()
        user = self.request.user
        
        # Handle unauthenticated requests
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # Debug print (remove after testing)
        print(f"DEBUG - User: {user.username}, Role: {user.role}, is_staff: {getattr(user, 'is_staff', False)}")
        
        # Check if user is admin/staff
        # METHOD 1: Check by is_staff field
        if getattr(user, 'is_staff', False):
            print("DEBUG - Admin detected via is_staff, returning all users")
            return queryset
        
        # METHOD 2: Fallback check by role (in case is_staff wasn't set)
        if user.role == User.ROLE_ADMIN:
            print("DEBUG - Admin detected via role, returning all users")
            return queryset
        
        # Regular users can only see their own profile
        print("DEBUG - Regular user, filtering to own profile only")
        return queryset.filter(id=user.id)

    def perform_create(self, serializer):
        """Create user with proper password hashing."""
        serializer.save()
    
    def perform_update(self, serializer):
        """Update user and track modification time."""
        serializer.save(updated_at=timezone.now())
    
    def perform_destroy(self, instance):
        """
        Soft delete - deactivate instead of actually deleting.
        This preserves data integrity and relationships.
        """
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
    
    @action(detail=False, methods=['get'], url_path='me')
    def current_user(self, request):
        """
        Get current authenticated user's profile with full details.
        
        GET /api/users/me/
        
        Returns:
            User profile with related data (user_profile or shop_profile)
        """
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """
        Change password for the current authenticated user.
        
        POST /api/users/change-password/
        Body: {
            "old_password": "current password",
            "new_password": "new password",
            "new_password_confirm": "new password again"
        }
        
        Returns:
            Success message or validation errors
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save(update_fields=['password', 'updated_at'])
            
            return Response({
                'message': 'Password changed successfully. Please login again with your new password.'
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """
        Suspend a user account (admin only).
        
        POST /api/users/{id}/suspend/
        
        Args:
            pk: User ID to suspend
        
        Returns:
            Success message or error
        """
        # Check admin permission
        if not hasattr(request.user, 'is_staff') or not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can suspend users.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        # Prevent self-suspension
        if user.id == request.user.id:
            return Response(
                {'error': 'You cannot suspend your own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already suspended
        if user.is_suspended:
            return Response(
                {'error': f'User {user.username} is already suspended.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Suspend user
        user.is_suspended = True
        user.is_active = False
        user.save(update_fields=['is_suspended', 'is_active', 'updated_at'])
        
        serializer = UserDetailSerializer(user)
        return Response({
            'message': f'User {user.username} has been suspended successfully.',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a suspended user account (admin only).
        
        POST /api/users/{id}/activate/
        
        Args:
            pk: User ID to activate
        
        Returns:
            Success message or error
        """
        # Check admin permission
        if not hasattr(request.user, 'is_staff') or not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can activate users.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        # Check if not suspended
        if not user.is_suspended:
            return Response(
                {'error': f'User {user.username} is not suspended.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Activate user
        user.is_suspended = False
        user.is_active = True
        user.save(update_fields=['is_suspended', 'is_active', 'updated_at'])
        
        serializer = UserDetailSerializer(user)
        return Response({
            'message': f'User {user.username} has been activated successfully.',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get comprehensive user statistics (admin only).
        
        GET /api/users/statistics/
        
        Returns:
            Dictionary with various user counts and statistics
        """
        # Check admin permission
        if not hasattr(request.user, 'is_staff') or not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can view statistics.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        suspended_users = User.objects.filter(is_suspended=True).count()
        regular_users = User.objects.filter(role=User.ROLE_USER).count()
        shop_users = User.objects.filter(role=User.ROLE_SHOP).count()
        
        # Additional statistics
        recent_users = User.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count()
        
        users_with_orders = User.objects.filter(
            user_profile__orders__isnull=False
        ).distinct().count()
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'suspended_users': suspended_users,
            'regular_users': regular_users,
            'shop_users': shop_users,
            'users_registered_last_30_days': recent_users,
            'users_with_orders': users_with_orders,
            'percentage_active': round((active_users / total_users * 100), 2) if total_users > 0 else 0,
        }
        
        return Response(stats, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='orders')
    def user_orders(self, request, pk=None):
        """
        Get all orders for a specific user.
        
        GET /api/users/{id}/orders/
        
        Args:
            pk: User ID
        
        Returns:
            List of orders with summary information
        """
        user = self.get_object()
        
        # Permission check: users can only see their own orders, admins can see all
        if user.id != request.user.id and not (hasattr(request.user, 'is_staff') and request.user.is_staff):
            return Response(
                {'error': 'You can only view your own orders.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user has a user_profile (not a shop user)
        if user.role != User.ROLE_USER or not hasattr(user, 'user_profile'):
            return Response(
                {'error': 'This user does not have a customer profile.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get orders with related data
        orders = Order.objects.filter(
            user_profile=user.user_profile
        ).select_related(
            'user_profile'
        ).prefetch_related(
            'shop_orders__shop_profile',
            'payments'
        ).order_by('-created_at')
        
        # Build response
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'order_name': order.order_name,
                'color_or_black': order.color_or_black,
                'landscape_or_portrait': order.landscape_or_portrait,
                'created_at': order.created_at,
                'status': 'pending' if order.shop_orders.exists() else 'created',
                'total_shops_assigned': order.shop_orders.count(),
            })
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'total_orders': orders.count(),
            'orders': orders_data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='search')
    def search_users(self, request):
        """
        Advanced user search (admin only).
        
        GET /api/users/search/?q=searchterm&role=user&status=active
        
        Query Parameters:
            q: Search term (username, email, shop name)
            role: Filter by role (user/shop)
            status: Filter by status (active/suspended)
        
        Returns:
            Filtered list of users
        """
        # Check admin permission
        if not hasattr(request.user, 'is_staff') or not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can search all users.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset()
        
        # Get query parameters
        search_term = request.query_params.get('q', None)
        role = request.query_params.get('role', None)
        status_filter = request.query_params.get('status', None)
        
        # Apply filters
        if search_term:
            queryset = queryset.filter(
                Q(username__icontains=search_term) |
                Q(user_profile__email__icontains=search_term) |
                Q(shop_profile__shop_name__icontains=search_term)
            )
        
        if role:
            queryset = queryset.filter(role=role)
        
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True, is_suspended=False)
        elif status_filter == 'suspended':
            queryset = queryset.filter(is_suspended=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    






from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile
from .serializers import UserProfileSerializer

class UserProfileViewSet(
    
    generics.RetrieveUpdateAPIView
):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)



from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile
from .serializers import UserProfileSerializer
class ShopProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/shop_profiles/{id}/
    PATCH /api/shop_profiles/{id}/
    PUT /api/shop_profiles/{id}/
    
    Retrieve or update a shop profile.
    Only shop owners can update their own profile.
    """
    queryset = ShopProfile.objects.all()
    serializer_class = ShopProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Get shop profile by ID and verify ownership
        """
        shop_id = self.kwargs.get('pk')
        shop_profile = get_object_or_404(ShopProfile, id=shop_id)

        # Check if user is admin or shop owner
        user = self.request.user
        if not (user.is_staff or shop_profile.user == user):
            self.permission_denied(self.request)

        return shop_profile

    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/shop_profiles/{id}/
        """
        shop_profile = self.get_object()
        serializer = self.get_serializer(shop_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """
        PUT /api/shop_profiles/{id}/
        Full update of shop profile
        """
        shop_profile = self.get_object()
        serializer = self.get_serializer(shop_profile, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/shop_profiles/{id}/
        Partial update of shop profile
        """
        shop_profile = self.get_object()
        serializer = self.get_serializer(
            shop_profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderCreateView(APIView):
    permission_classes=[IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # handle file uploads

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        


class OrderListView(generics.ListAPIView):
    """Only for listing orders"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # user = self.request.user
        # print(f"🔍 Logged-in user: {user.username}, ID: {user.id}")
        
        # if user.is_staff:
        #     print("✅ Admin user - returning all orders")
        return Order.objects.all()
        
        # if hasattr(user, 'user_profile'):
        #     user_profile_id = user.user_profile.id
        #     print(f"👤 User profile ID: {user_profile_id}")
        #     orders = Order.objects.filter(user_profile=user.user_profile)
        #     print(f"📦 Found {orders.count()} orders for this user")
        #     return orders
        
        # print("❌ User has no profile - returning empty queryset")
        # return Order.objects.none()


class ShopProfileViewTest(generics.ListAPIView):
    serializer_class = ShopProfileSerializer
    def get_queryset(self):
        return ShopProfile.objects.all()

class ShopListView(generics.ListAPIView):
    """
    GET /api/shops/ - List all active shops for dropdown
    """
    serializer_class = ShopProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Return only active, non-suspended shops
        return ShopProfile.objects.filter(
            is_active=True,
            is_suspended=False
        ).select_related('user').order_by('shop_name')
    


from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import ShopOrder, Order
from .serializers import (
    ShopOrderListSerializer,
    ShopOrderDetailSerializer,
    ShopOrderUpdateSerializer,
)
from .permissions import IsOwnerOrAdmin


from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import ShopOrder, Order, ShopProfile
from .serializers import (
    ShopOrderListSerializer,
    ShopOrderDetailSerializer,
    ShopOrderUpdateSerializer,
)


class ShopOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order__order_name', 'shop_profile__shop_name']
    filterset_fields = ['status', 'shop_profile']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ShopOrderDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return ShopOrderUpdateSerializer
        return ShopOrderListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return ShopOrder.objects.all().select_related(
                'shop_profile__user',
                'order__user_profile__user',
                'order__selected_shop'
            )
        if user.role == 'shop':
            try:
                shop_profile = ShopProfile.objects.get(user_id=user.id)
                return ShopOrder.objects.filter(
                    shop_profile=shop_profile
                ).select_related(
                    'shop_profile__user',
                    'order__user_profile__user',
                    'order__selected_shop'
                )
            except ShopProfile.DoesNotExist:
                return ShopOrder.objects.none()
        return ShopOrder.objects.none()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return obj
        if user.role == 'shop':
            try:
                shop_profile = ShopProfile.objects.get(user_id=user.id)
                if obj.shop_profile == shop_profile:
                    return obj
            except ShopProfile.DoesNotExist:
                pass
        self.permission_denied(self.request)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def accept(self, request, pk=None):
        shop_order = self.get_object()
        if shop_order.status != ShopOrder.STATUS_PENDING:
            return Response({'error': 'Can only accept pending orders'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.data.get('quoted_price'):
            return Response({'error': 'quoted_price is required'}, status=status.HTTP_400_BAD_REQUEST)
        shop_order.status = ShopOrder.STATUS_ACCEPTED
        shop_order.quoted_price = request.data.get('quoted_price')
        shop_order.estimated_completion = request.data.get('estimated_completion')
        shop_order.save()
        serializer = self.get_serializer(shop_order)
        return Response({'message': 'Order accepted successfully', 'data': serializer.data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        shop_order = self.get_object()
        if shop_order.status != ShopOrder.STATUS_PENDING:
            return Response({'error': 'Can only reject pending orders'}, status=status.HTTP_400_BAD_REQUEST)
        shop_order.status = ShopOrder.STATUS_REJECTED
        shop_order.save()
        return Response({'message': 'Order rejected successfully'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request):
        queryset = self.get_queryset()
        data = {
            'total_orders': queryset.count(),
            'pending': queryset.filter(status=ShopOrder.STATUS_PENDING).count(),
            'accepted': queryset.filter(status=ShopOrder.STATUS_ACCEPTED).count(),
            'rejected': queryset.filter(status=ShopOrder.STATUS_REJECTED).count(),
            'total_quoted_value': sum(o.quoted_price or 0 for o in queryset)
        }
        return Response(data, status=status.HTTP_200_OK)


class ShopOrdersByShopProfileView(generics.ListAPIView):
    """
    Simple view to fetch orders by shop profile ID.
    
    GET /api/shops/{shop_id}/orders/
    
    Returns all ShopOrder entries for a specific shop.
    Shows which orders were sent to that shop.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Get shop_id from URL parameter
        shop_id = self.kwargs.get('shop_id')
        
        print(f"🔍 Fetching orders for shop_id: {shop_id}")
        
        # Verify shop exists
        shop = get_object_or_404(ShopProfile, id=shop_id)
        print(f"✅ Found shop: {shop.shop_name}")
        
        # Get all ShopOrder entries for this shop
        shop_orders = ShopOrder.objects.filter(
            shop_profile_id=shop_id
        ).select_related('order__user_profile__user', 'order__selected_shop')
        
        print(f"📦 Found {shop_orders.count()} shop orders")
        
        # Extract the actual orders from ShopOrder
        orders = Order.objects.filter(
            shop_orders__shop_profile_id=shop_id
        ).distinct().select_related('user_profile__user', 'selected_shop')
        
        print(f"📋 Extracted {orders.count()} unique orders")
        
        return orders










class StoreListCreateView(generics.ListCreateAPIView):
    queryset = Store.objects.select_related("shop_profile").all()
    serializer_class = StoreSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "store_type"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]


class StoreRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Store.objects.select_related("shop_profile").all()
    serializer_class = StoreSerializer




class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related("store").all()
    serializer_class = ProductSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["store", "is_active"]
    search_fields = ["name", "sku"]
    ordering_fields = ["price", "created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()

        store_id = self.request.query_params.get("store_id")
        if store_id:
            queryset = queryset.filter(store_id=store_id)

        return queryset



class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("store").all()
    serializer_class = ProductSerializer


from django.db.models import Prefetch

class StoreWithProductsListView(generics.ListAPIView):
    serializer_class = PrdouctStoreVise

    def get_queryset(self):
        return Store.objects.filter(is_open=True).prefetch_related(
            Prefetch(
                "products",
                queryset=Product.objects.filter(is_active=True)
            )
        )



class StoreProductsListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        store_id = self.kwargs["store_id"]
        return Product.objects.filter(store_id=store_id, is_active=True).order_by("name")






# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from decimal import Decimal

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_multi_store_order(request):
    """
    Create orders for multiple stores from shopping cart.
    
    Expected payload:
    {
      "orders": [
        {
          "store_id": 1,
          "items": [{"product_id": 1, "quantity": 2}],
          "is_delivery": false,
          "delivery_address_text": "",
          "pickup_note": ""
        }
      ]
    }
    """
    try:
        user = request.user
        user_profile = UserProfile.objects.get(user=user)
        orders_data = request.data.get('orders', [])
        
        if not orders_data:
            return Response(
                {"error": "No orders provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_orders = []
        
        with transaction.atomic():
            for order_data in orders_data:
                store_id = order_data.get('store_id')
                items_data = order_data.get('items', [])
                
                # Validate store
                try:
                    store = Store.objects.select_related('shop_profile').get(
                        id=store_id,
                        is_open=True
                    )
                except Store.DoesNotExist:
                    raise ValueError(f"Store {store_id} not found or closed")
                
                if not items_data:
                    raise ValueError(f"No items for store {store_id}")
                
                # Calculate totals and validate products
                subtotal = Decimal('0.00')
                order_items = []
                
                for item_data in items_data:
                    product_id = item_data.get('product_id')
                    quantity = item_data.get('quantity', 1)
                    
                    try:
                        product = Product.objects.get(
                            id=product_id,
                            store=store,
                            is_active=True
                        )
                    except Product.DoesNotExist:
                        raise ValueError(f"Product {product_id} not found in store {store.name}")
                    
                    # Check stock
                    if product.stock_qty < quantity:
                        raise ValueError(
                            f"Insufficient stock for {product.name}. "
                            f"Available: {product.stock_qty}, Requested: {quantity}"
                        )
                    
                    line_total = product.price * quantity
                    subtotal += line_total
                    
                    order_items.append({
                        'product': product,
                        'quantity': quantity,
                        'unit_price': product.price,
                        'line_total': line_total
                    })
                
                # Calculate delivery fee
                is_delivery = order_data.get('is_delivery', False)
                delivery_fee = Decimal('29.00') if is_delivery else Decimal('0.00')
                total = subtotal + delivery_fee
                
                # Create ProductOrder
                product_order = ProductOrder.objects.create(
                    user_profile=user_profile,
                    store=store,
                    status=ProductOrder.STATUS_CREATED,
                    is_delivery=is_delivery,
                    delivery_address_text=order_data.get('delivery_address_text', ''),
                    pickup_note=order_data.get('pickup_note', ''),
                    subtotal=subtotal,
                    delivery_fee=delivery_fee,
                    total=total
                )
                
                # Create ProductOrderItems
                for item in order_items:
                    ProductOrderItem.objects.create(
                        order=product_order,
                        product=item['product'],
                        product_name_snapshot=item['product'].name,
                        product_sku_snapshot=item['product'].sku or '',
                        unit_price_snapshot=item['unit_price'],
                        qty=item['quantity'],
                        line_total=item['line_total']
                    )
                    
                    # Reduce stock
                    item['product'].stock_qty -= item['quantity']
                    item['product'].save()
                
                # Create Delivery record if needed
                if is_delivery:
                    Delivery.objects.create(
                        order=product_order,
                        delivery_address=order_data.get('delivery_address_text', ''),
                        customer_phone=user_profile.phone
                    )
                
                # Log initial status
                OrderStatusLog.objects.create(
                    order=product_order,
                    from_status='',
                    to_status=ProductOrder.STATUS_CREATED,
                    notes='Order created from cart'
                )
                
                created_orders.append({
                    'order_id': product_order.id,
                    'order_number': product_order.order_number,
                    'store_id': store.id,
                    'store_name': store.name,
                    'items_count': len(order_items),
                    'subtotal': str(product_order.subtotal),
                    'delivery_fee': str(product_order.delivery_fee),
                    'total': str(product_order.total),
                    'status': product_order.status
                })
        
        return Response({
            'success': True,
            'message': f'{len(created_orders)} order(s) created successfully',
            'orders': created_orders
        }, status=status.HTTP_201_CREATED)
    
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except UserProfile.DoesNotExist:
        return Response(
            {"error": "User profile not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Failed to create orders: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_orders(request):
    """
    Get all orders for the authenticated user with full details.
    Returns orders grouped by store with items.
    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        
        # Get all orders with related data
        orders = ProductOrder.objects.filter(
            user_profile=user_profile
        ).select_related(
            'store',
            'store__shop_profile'
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=ProductOrderItem.objects.select_related('product')
            )
        ).order_by('-created_at')
        
        # Format response
        orders_data = []
        for order in orders:
            orders_data.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'store': {
                    'id': order.store.id,
                    'name': order.store.name,
                    'type': order.store.store_type,
                    'shop_name': order.store.shop_profile.shop_name,
                },
                'status': order.status,
                'status_display': order.get_status_display(),
                'is_delivery': order.is_delivery,
                'delivery_address': order.delivery_address_text,
                'pickup_note': order.pickup_note,
                'subtotal': str(order.subtotal),
                'delivery_fee': str(order.delivery_fee),
                'total': str(order.total),
                'items': [
                    {
                        'id': item.id,
                        'product_id': item.product.id,
                        'name': item.product_name_snapshot,
                        'sku': item.product_sku_snapshot,
                        'quantity': item.qty,
                        'unit_price': str(item.unit_price_snapshot),
                        'line_total': str(item.line_total),
                    }
                    for item in order.items.all()
                ],
                'tracking': {
                    'confirmed_at': order.confirmed_at.isoformat() if order.confirmed_at else None,
                    'preparing_at': order.preparing_at.isoformat() if order.preparing_at else None,
                    'ready_at': order.ready_at.isoformat() if order.ready_at else None,
                    'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
                    'cancelled_at': order.cancelled_at.isoformat() if order.cancelled_at else None,
                },
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
            })
        
        return Response({
            'success': True,
            'count': len(orders_data),
            'orders': orders_data
        }, status=status.HTTP_200_OK)
    
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to fetch orders: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_detail(request, order_id):
    """
    Get detailed information for a specific order.
    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        
        order = ProductOrder.objects.select_related(
            'store',
            'store__shop_profile'
        ).prefetch_related(
            'items__product',
            'status_logs'
        ).get(
            id=order_id,
            user_profile=user_profile
        )
        
        # Get delivery info if exists
        delivery_info = None
        if hasattr(order, 'delivery'):
            delivery = order.delivery
            delivery_info = {
                'tracking_code': delivery.tracking_code,
                'estimated_delivery_time': delivery.estimated_delivery_time.isoformat() if delivery.estimated_delivery_time else None,
                'actual_delivery_time': delivery.actual_delivery_time.isoformat() if delivery.actual_delivery_time else None,
                'delivery_person_phone': delivery.delivery_person_phone,
                'is_completed': delivery.is_completed,
            }
        
        # Get status timeline
        status_timeline = [
            {
                'from_status': log.from_status,
                'to_status': log.to_status,
                'notes': log.notes,
                'changed_at': log.changed_at.isoformat(),
            }
            for log in order.status_logs.all()
        ]
        
        return Response({
            'success': True,
            'order': {
                'order_id': order.id,
                'order_number': order.order_number,
                'store': {
                    'id': order.store.id,
                    'name': order.store.name,
                    'type': order.store.store_type,
                    'shop_name': order.store.shop_profile.shop_name,
                    'phone': order.store.shop_profile.phone,
                },
                'status': order.status,
                'status_display': order.get_status_display(),
                'items': [
                    {
                        'name': item.product_name_snapshot,
                        'sku': item.product_sku_snapshot,
                        'quantity': item.qty,
                        'unit_price': str(item.unit_price_snapshot),
                        'line_total': str(item.line_total),
                        'special_instructions': item.special_instructions,
                    }
                    for item in order.items.all()
                ],
                'subtotal': str(order.subtotal),
                'delivery_fee': str(order.delivery_fee),
                'total': str(order.total),
                'is_delivery': order.is_delivery,
                'delivery_address': order.delivery_address_text,
                'pickup_note': order.pickup_note,
                'delivery': delivery_info,
                'status_timeline': status_timeline,
                'created_at': order.created_at.isoformat(),
            }
        }, status=status.HTTP_200_OK)
    
    except ProductOrder.DoesNotExist:
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch, Q

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vendor_store_orders(request):
    """
    Return orders for the authenticated vendor's stores only.
    
    Optional query params:
    - status: filter by order status (created, confirmed, preparing, ready, out_for_delivery, delivered, cancelled)
    - store_id: filter to a single store (must belong to this vendor)
    """
    try:
        # Ensure this user is a shop/vendor
        if request.user.role != User.ROLE_SHOP:
            return Response(
                {"error": "Only shop users can access store orders"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get vendor's ShopProfile
        try:
            shop_profile = ShopProfile.objects.get(user=request.user)
        except ShopProfile.DoesNotExist:
            return Response(
                {"error": "Shop profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Base queryset: orders for any store belonging to this shop_profile
        orders = (
            ProductOrder.objects.filter(store__shop_profile=shop_profile)
            .select_related("store", "user_profile__user")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=ProductOrderItem.objects.select_related("product"),
                )
            )
            .order_by("-created_at")
        )

        # Optional filters
        status_param = request.GET.get("status")
        if status_param:
            orders = orders.filter(status=status_param)

        store_id_param = request.GET.get("store_id")
        if store_id_param:
            orders = orders.filter(store_id=store_id_param)

        # Serialize
        data = []
        for order in orders:
            data.append(
                {
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "store": {
                        "id": order.store.id,
                        "name": order.store.name,
                        "type": order.store.store_type,
                    },
                    "customer": {
                        "id": order.user_profile.id,
                        "username": order.user_profile.user.username,
                        "phone": order.user_profile.phone,
                        "college": order.user_profile.college,
                    },
                    "status": order.status,
                    "status_display": order.get_status_display(),
                    "is_delivery": order.is_delivery,
                    "delivery_address": order.delivery_address_text,
                    "pickup_note": order.pickup_note,
                    "subtotal": str(order.subtotal),
                    "delivery_fee": str(order.delivery_fee),
                    "total": str(order.total),
                    "items": [
                        {
                            "id": item.id,
                            "product_id": item.product.id,
                            "name": item.product_name_snapshot,
                            "sku": item.product_sku_snapshot,
                            "quantity": item.qty,
                            "unit_price": str(item.unit_price_snapshot),
                            "line_total": str(item.line_total),
                        }
                        for item in order.items.all()
                    ],
                    "created_at": order.created_at.isoformat(),
                }
            )

        return Response(
            {
                "success": True,
                "count": len(data),
                "orders": data,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return Response(
            {"error": f"Failed to fetch vendor orders: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_push_token(request):
    """
    POST /api/push-token/
    Body: { "token": "ExponentPushToken[xxx]" }
    """
    token = request.data.get('token', '').strip()
    if not token:
        return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
    UserPushToken.objects.update_or_create(token=token, defaults={'user': request.user})
    return Response({'success': True, 'message': 'Push token registered.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_cancel_order(request, order_id):
    """
    Customer cancels their own order.
    POST /api/product-orders/<order_id>/cancel/
    Body: { "reason": "Changed my mind" }
    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        order = ProductOrder.objects.get(id=order_id, user_profile=user_profile)
    except UserProfile.DoesNotExist:
        return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except ProductOrder.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    # Users can only cancel before it starts preparing
    cancellable_statuses = [ProductOrder.STATUS_CREATED, ProductOrder.STATUS_CONFIRMED]
    if order.status not in cancellable_statuses:
        return Response(
            {'error': f'Cannot cancel. Order is already "{order.status}". Cancel only allowed before preparation starts.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'error': 'Please provide a cancellation reason.'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # Restore stock
        for item in order.items.select_related('product').all():
            item.product.stock_qty += item.qty
            item.product.save()

        order.cancellation_reason = reason
        order.update_status(
            ProductOrder.STATUS_CANCELLED,
            notes=f"Cancelled by customer: {reason}",
            cancelled_by=ProductOrder.CANCELLED_BY_USER
        )

    return Response({
        'success': True,
        'message': 'Order cancelled successfully.',
        'order_number': order.order_number,
        'cancelled_by': 'customer',
        'reason': reason
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vendor_cancel_order(request, order_id):
    """
    Vendor cancels an order assigned to their store.
    POST /api/vendor/product-orders/<order_id>/cancel/
    Body: { "reason": "Out of stock" }
    """
    if request.user.role != User.ROLE_SHOP:
        return Response({'error': 'Only vendors can use this endpoint.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        shop_profile = ShopProfile.objects.get(user=request.user)
        order = ProductOrder.objects.get(id=order_id, store__shop_profile=shop_profile)
    except ShopProfile.DoesNotExist:
        return Response({'error': 'Shop profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except ProductOrder.DoesNotExist:
        return Response({'error': 'Order not found or does not belong to your store.'}, status=status.HTTP_404_NOT_FOUND)

    # Vendors cannot cancel if already delivered or already cancelled
    non_cancellable = [ProductOrder.STATUS_DELIVERED, ProductOrder.STATUS_CANCELLED, ProductOrder.STATUS_REFUNDED]
    if order.status in non_cancellable:
        return Response(
            {'error': f'Cannot cancel an order with status "{order.status}".'},
            status=status.HTTP_400_BAD_REQUEST
        )

    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'error': 'Please provide a cancellation reason.'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # Restore stock
        for item in order.items.select_related('product').all():
            item.product.stock_qty += item.qty
            item.product.save()

        order.cancellation_reason = reason
        order.update_status(
            ProductOrder.STATUS_CANCELLED,
            notes=f"Cancelled by vendor: {reason}",
            cancelled_by=ProductOrder.CANCELLED_BY_VENDOR
        )

    return Response({
        'success': True,
        'message': 'Order cancelled successfully.',
        'order_number': order.order_number,
        'cancelled_by': 'vendor',
        'reason': reason
    }, status=status.HTTP_200_OK)
