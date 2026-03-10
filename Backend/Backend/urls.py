
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from print.views import *
from django.conf import settings
from django.conf.urls.static import static
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'shop-orders', ShopOrderViewSet, basename='shop-order')
# Users: Core Endpoints for Registration, CRUD, and Info ---------------------------------------
# POST   /api/users/                        # Create/Register a new user (PUBLIC)
# GET    /api/users/                        # List users (admin: all users, normal: self)
# GET    /api/users/{id}/                   # Retrieve user by id
# PATCH  /api/users/{id}/                   # Update user (admin: anyone, normal: self)
# PUT    /api/users/{id}/                   # Full update user (admin: anyone, normal: self)
# DELETE /api/users/{id}/                   # Deactivate (soft-delete) user

# Profiles (User and Shop, PATCH for info update) ----------------------------------------------
# PATCH  /api/user_profiles/{id}/           # Update customer profile (address/phone/email/college)
# PATCH  /api/shop_profiles/{id}/           # Update shop user profile

# Auth/Account Management ----------------------------------------------------------
# GET    /api/users/me/                     # Get currently logged-in user's info
# POST   /api/users/change-password/        # Change current user password

# Admin/Owner Actions -------------------------------------------------------------
# POST   /api/users/{id}/suspend/           # Suspend (disable) a user (admin only)
# POST   /api/users/{id}/activate/          # Activate (restore) a user (admin only)
# GET    /api/users/statistics/             # View user statistics (admin only)
# GET    /api/users/search/?...             # Search/filter/list users (admin only)

# Orders / User Details -----------------------------------------------------------
# GET    /api/users/{id}/orders/            # Get all orders for specific user (admin/self)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/login/', LoginAPIView.as_view(), name='login'),
    path('api/auth/refresh/', RefreshTokenAPIView.as_view(), name='token_refresh'),
    path('api/auth/logout/', LogoutAPIView.as_view(), name='logout'),
    path('api/user_profiles/<int:pk>/',UserProfileViewSet.as_view()),
    path('api/shop_profile/<int:pk>/',ShopProfileDetailView.as_view()),
    path('userprofiles/',ShopProfileViewTest.as_view()),
    path('api/orders/',OrderCreateView.as_view(),name='order-create'),
    path('api/orders/list/',OrderListView.as_view(),name='order-create'),
    path('api/shops/',ShopListView.as_view(),name='shop create'),
    path('api/shops/<int:shop_id>/orders/', ShopOrdersByShopProfileView.as_view(), name='shop-orders'),
    path("api/stores/", StoreListCreateView.as_view(), name="store-list-create"),
    path("api/stores/<int:pk>/", StoreRetrieveUpdateDestroyView.as_view(), name="store-detail"),

    # 📦 Product
    path("api/products/", ProductListCreateView.as_view(), name="product-list-create"),
    path("api/products/<int:pk>/", ProductRetrieveUpdateDestroyView.as_view(), name="product-detail"),
    path(
    "stores-with-products/",
    StoreWithProductsListView.as_view(),
    name="stores-with-products"
),
     path("api/stores/<int:store_id>/products/", StoreProductsListAPIView.as_view(), name="store-products"),
     path('api/orders/create/', create_multi_store_order, name='create_orders'),
      path('api/orders/my-orders/', get_user_orders, name='get_user_orders'),
    path('api/orders/<int:order_id>/', get_order_detail, name='get_order_detail'),
    path(
        "api/vendor/store-orders/",
        get_vendor_store_orders,
        name="get_vendor_store_orders",
    ),
    path('api/product-orders/<int:order_id>/cancel/', user_cancel_order, name='user-cancel-order'),
path('api/vendor/product-orders/<int:order_id>/cancel/', vendor_cancel_order, name='vendor-cancel-order'),

path('push-token/', register_push_token, name='register-push-token'),
path(
    'api/vendor/product-orders/<int:order_id>/update-status/',
    vendor_update_order_status,
    name='vendor-update-order-status'
),
path('api/orders/<int:order_id>/create-payment/',  create_product_payment,   name='create-product-payment'),
path('api/orders/<int:order_id>/verify-payment/',  verify_product_payment,    name='verify-product-payment'),
path('api/orders/<int:order_id>/payment-status/',  product_payment_status,    name='product-payment-status'),

    
]+ (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else [])


