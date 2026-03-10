from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password
import uuid

# models.py - CORRECTED VERSION
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password

# models.py - COMPLETE FIXED User Model
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    """
    Custom user model for authentication and role management.
    Compatible with AUTH_USER_MODEL setting.
    """
    # Role Constants
    ROLE_USER = 'user'
    ROLE_SHOP = 'shop'
    ROLE_ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (ROLE_USER, _('User')),
        (ROLE_SHOP, _('Shop')),
        (ROLE_ADMIN, _('Admin')),
    ]
    
    # Core fields
    username = models.CharField(max_length=150, unique=True, db_index=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, db_index=True)
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # REQUIRED for AUTH_USER_MODEL - ADD THESE!
    USERNAME_FIELD = 'username'  # Field used for authentication
    REQUIRED_FIELDS = []  # Fields required when creating superuser (empty if only username needed)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username', 'role']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def set_password(self, raw_password):
        """Hash and set the password."""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if the provided password matches the stored hash."""
        return check_password(raw_password, self.password)
    
    def save(self, *args, **kwargs):
        """Override save to hash password and set is_staff."""
        if self.password and not self.password.startswith('pbkdf2_'):
            self.set_password(self.password)
        
        # Auto-set is_staff for admin role
        self.is_staff = (self.role == self.ROLE_ADMIN)
        
        super().save(*args, **kwargs)
    
    # REQUIRED for AUTH_USER_MODEL - ADD THESE PROPERTIES!
    @property
    def is_authenticated(self):
        """Always return True for authenticated users."""
        return True
    
    @property
    def is_anonymous(self):
        """Always return False for authenticated users."""
        return False
    
    # OPTIONAL but recommended for Django admin
    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        return self.is_staff
    
    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        return self.is_staff
    
    # OPTIONAL: Make the model compatible with Django's user system
    def get_username(self):
        """Return the username for this User."""
        return self.username


# Keep all other models exactly as they are (UserProfile, ShopProfile, Order, etc.)
class UserProfile(models.Model):
    """Extended profile information for regular users."""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_profile',
        limit_choices_to={'role': User.ROLE_USER}
    )
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=15, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    college = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.email}"


class ShopProfile(models.Model):
    """Extended profile information for shop owners."""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='shop_profile',
        limit_choices_to={'role': User.ROLE_SHOP}
    )
    shop_name = models.CharField(max_length=200, db_index=True)
    address = models.TextField()
    phone = models.CharField(max_length=15, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    gst_number = models.CharField(max_length=15, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shop_profiles'
        verbose_name = 'Shop Profile'
        verbose_name_plural = 'Shop Profiles'
        indexes = [
            models.Index(fields=['shop_name', 'is_active']),
        ]
    
    def __str__(self):
        return self.shop_name

# All other models (Order, ShopOrder, Payment, Invoice, Commission) remain unchanged

    """
    Extended profile information for shop owners.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='shop_profile',
        limit_choices_to={'role': User.ROLE_SHOP}
    )
    shop_name = models.CharField(max_length=200, db_index=True)
    address = models.TextField()
    phone = models.CharField(max_length=15, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    gst_number = models.CharField(max_length=15, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shop_profiles'
        verbose_name = 'Shop Profile'
        verbose_name_plural = 'Shop Profiles'
        indexes = [
            models.Index(fields=['shop_name', 'is_active']),
        ]
    
    def __str__(self):
        return self.shop_name


class Order(models.Model):
    """
    Customer print orders with file and printing preferences.
    """
    # Color Choices
    COLOR_BLACK = False
    COLOR_COLORED = True
    
    # Orientation Choices
    ORIENTATION_PORTRAIT = False
    ORIENTATION_LANDSCAPE = True
    
    order_name = models.CharField(max_length=200)
    file_path = models.FileField(upload_to='orders/%Y/%m/%d/')
    pages_selected = models.CharField(max_length=100, help_text=_("e.g., 1-5, 10, 15-20"))
    color_or_black = models.BooleanField(
        default=COLOR_BLACK,
        help_text=_("False=Black & White, True=Color")
    )
    landscape_or_portrait = models.BooleanField(
        default=ORIENTATION_PORTRAIT,
        help_text=_("False=Portrait, True=Landscape")
    )
    user_profile = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
   
    selected_shop = models.ForeignKey(
        ShopProfile,
        on_delete=models.SET_NULL,
        related_name='confirmed_orders',
        null=True,
        blank=True,
        help_text=_("Shop chosen by user after seeing responses")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_profile', '-created_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.id}: {self.order_name}"


class ShopOrder(models.Model):
    """
    Junction table tracking which shops received which orders.
    """
    # Status Constants
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_ACCEPTED, _('Accepted')),
        (STATUS_REJECTED, _('Rejected')),
    ]
    
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='shop_orders'
    )
    shop_profile = models.ForeignKey(
        ShopProfile, 
        on_delete=models.CASCADE, 
        related_name='received_orders'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shop_orders'
        verbose_name = 'Shop Order'
        verbose_name_plural = 'Shop Orders'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'shop_profile'],
                name='unique_shop_order'
            )
        ]
        indexes = [
            models.Index(fields=['shop_profile', 'status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Shop Order #{self.id} - {self.get_status_display()}"


class Payment(models.Model):
    """
    Payment transactions for completed orders.
    """
    # Payment Method Constants
    METHOD_UPI = 'UPI'
    METHOD_CARD = 'Card'
    METHOD_CASH = 'Cash'
    METHOD_NET_BANKING = 'NetBanking'
    
    PAYMENT_METHOD_CHOICES = [
        (METHOD_UPI, _('UPI')),
        (METHOD_CARD, _('Card')),
        (METHOD_CASH, _('Cash')),
        (METHOD_NET_BANKING, _('Net Banking')),
    ]
    
    # Status Constants
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    
    PAYMENT_STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_FAILED, _('Failed')),
        (STATUS_REFUNDED, _('Refunded')),
    ]
    
    order = models.ForeignKey(
        Order, 
        on_delete=models.PROTECT, 
        related_name='payments'
    )
    user_profile = models.ForeignKey(
        UserProfile, 
        on_delete=models.PROTECT, 
        related_name='payments'
    )
    shop_profile = models.ForeignKey(
        ShopProfile, 
        on_delete=models.PROTECT, 
        related_name='received_payments'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default=STATUS_PENDING,
        db_index=True
    )
    transaction_id = models.CharField(
        max_length=100, 
        unique=True, 
        blank=True, 
        null=True,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_status', '-created_at']),
            models.Index(fields=['shop_profile', 'payment_status']),
        ]
    
    def __str__(self):
        return f"Payment #{self.id} - {self.get_payment_status_display()} - ₹{self.amount}"


class Invoice(models.Model):
    """
    Generated invoices for payments with tax calculations.
    """
    # Status Constants
    STATUS_GENERATED = 'generated'
    STATUS_PAID = 'paid'
    STATUS_REFUNDED = 'refunded'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_GENERATED, _('Generated')),
        (STATUS_PAID, _('Paid')),
        (STATUS_REFUNDED, _('Refunded')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]
    
    payment = models.OneToOneField(
        Payment, 
        on_delete=models.PROTECT, 
        related_name='invoice'
    )
    order = models.ForeignKey(
        Order, 
        on_delete=models.PROTECT, 
        related_name='invoices'
    )
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    invoice_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=STATUS_GENERATED,
        db_index=True
    )
    pdf_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['status', '-invoice_date']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.get_status_display()}"


class Commission(models.Model):
    """
    Commission tracking and distribution between admin and shops.
    """
    # Status Constants
    STATUS_PENDING = 'pending'
    STATUS_ADMIN_PAID = 'admin_paid'
    STATUS_SHOP_PAID = 'shop_paid'
    STATUS_COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_ADMIN_PAID, _('Paid to Admin')),
        (STATUS_SHOP_PAID, _('Paid to Shop')),
        (STATUS_COMPLETED, _('Completed')),
    ]
    
    payment = models.OneToOneField(
        Payment, 
        on_delete=models.PROTECT, 
        related_name='commission'
    )
    shop_profile = models.ForeignKey(
        ShopProfile, 
        on_delete=models.PROTECT, 
        related_name='commissions'
    )
    admin_share = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.00)]
    )
    shop_share = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.00)]
    )
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=18.00,
        validators=[MinValueValidator(0.00)]
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=STATUS_PENDING,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commissions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['shop_profile', 'status']),
        ]
    
    def __str__(self):
        return f"Commission #{self.id} - {self.get_status_display()} - Shop: ₹{self.shop_share}"




class Store(models.Model):
    STORE_CAFETERIA = "cafeteria"
    STORE_STATIONERY = "stationery"
    STORE_PRINT = "print"
    STORE_TYPES = [(STORE_CAFETERIA, "Cafeteria"), (STORE_STATIONERY, "Stationery"), (STORE_PRINT, "Print Center")]

    shop_profile = models.ForeignKey(ShopProfile, on_delete=models.CASCADE, related_name="stores")
    name = models.CharField(max_length=200, db_index=True)
    store_type = models.CharField(max_length=30, choices=STORE_TYPES, db_index=True)
    is_open = models.BooleanField(default=True, db_index=True)
    location_hint = models.CharField(max_length=200, blank=True)  # e.g., "Main Block - Ground floor"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200, db_index=True)
    sku = models.CharField(max_length=64, blank=True, db_index=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])
    is_active = models.BooleanField(default=True, db_index=True)
    stock_qty = models.IntegerField(default=0)  # keep simple; if cafeteria, you can ignore or set high
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# Add after your existing models
class UserPushToken(models.Model):
    """Stores Expo push tokens per user device."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_tokens')
    token = models.CharField(max_length=200, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_push_tokens'

    def __str__(self):
        return f"{self.user.username} - {self.token[:30]}"
class Notification(models.Model):
    TYPE_ORDER_CANCELLED = 'order_cancelled'
    TYPE_ORDER_STATUS = 'order_status'
    TYPE_ORDER_CONFIRMED = 'order_confirmed'
    TYPE_GENERAL = 'general'

    TYPE_CHOICES = [
        (TYPE_ORDER_CANCELLED, 'Order Cancelled'),
        (TYPE_ORDER_STATUS, 'Order Status Update'),
        (TYPE_ORDER_CONFIRMED, 'Order Confirmed'),
        (TYPE_GENERAL, 'General'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, default=TYPE_GENERAL, db_index=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    related_order_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title}"


class ProductOrder(models.Model):
    """
    ENHANCED: Main order record with comprehensive tracking.
    """
    STATUS_CREATED = "created"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PREPARING = "preparing"
    STATUS_READY = "ready"
    STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_PREPARING, "Preparing"),
        (STATUS_READY, "Ready for Pickup"),
        (STATUS_OUT_FOR_DELIVERY, "Out for Delivery"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    # Core relationships
    user_profile = models.ForeignKey(
        UserProfile, 
        on_delete=models.PROTECT, 
        related_name="product_orders"
    )
    store = models.ForeignKey(
        Store, 
        on_delete=models.PROTECT, 
        related_name="orders"
    )
    
    # Order identification
    order_number = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,

    default=uuid.uuid4,
    editable=False,
        help_text="e.g., ORD-20260218-001234"
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=30, 
        choices=STATUS_CHOICES, 
        default=STATUS_CREATED, 
        db_index=True
    )
    
    # Delivery/pickup details
    is_delivery = models.BooleanField(default=False)
    delivery_address_text = models.TextField(blank=True)
    pickup_note = models.CharField(max_length=200, blank=True)
    
    # Financial details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status timestamps
    confirmed_at = models.DateTimeField(null=True, blank=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    # Inside your existing ProductOrder model — add these 2 fields:
    is_paid = models.BooleanField(default=False, db_index=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    
    # Additional tracking
    estimated_ready_time = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Vendor's estimate for when order will be ready"
    )
    customer_notes = models.TextField(blank=True)
    vendor_notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Ratings (optional)
    customer_rating = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    customer_review = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Add inside ProductOrder model alongside other fields
    CANCELLED_BY_USER = 'user'
    CANCELLED_BY_VENDOR = 'vendor'
    CANCELLED_BY_ADMIN = 'admin'

    CANCELLED_BY_CHOICES = [
        (CANCELLED_BY_USER, 'Customer'),
        (CANCELLED_BY_VENDOR, 'Vendor'),
        (CANCELLED_BY_ADMIN, 'Admin'),
    ]
    

    cancelled_by = models.CharField(
        max_length=10,
        choices=CANCELLED_BY_CHOICES,
        null=True,
        blank=True
    )
    quoted_price = models.DecimalField(
    max_digits=10, decimal_places=2,
    null=True, blank=True,
    help_text="Vendor's quoted price; triggers financial recalculation"
)
    
    class Meta:
        db_table = 'product_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_profile', '-created_at']),
            models.Index(fields=['store', 'status', '-created_at']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.store.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate order number
        if not self.order_number:
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            import random
            random_suffix = random.randint(100000, 999999)
            self.order_number = f"ORD-{timestamp}-{random_suffix}"
        super().save(*args, **kwargs)
    
    def update_status(self, new_status, notes="", cancelled_by=None):
        from django.utils import timezone
        old_status = self.status
        self.status = new_status

        timestamp_map = {
            self.STATUS_CONFIRMED: 'confirmed_at',
            self.STATUS_PREPARING: 'preparing_at',
            self.STATUS_READY: 'ready_at',
            self.STATUS_OUT_FOR_DELIVERY: 'out_for_delivery_at',
            self.STATUS_DELIVERED: 'delivered_at',
            self.STATUS_CANCELLED: 'cancelled_at',
        }
        if new_status in timestamp_map:
            setattr(self, timestamp_map[new_status], timezone.now())

        if cancelled_by:
            self.cancelled_by = cancelled_by

        self.save()

        OrderStatusLog.objects.create(
            order=self,
            from_status=old_status,
            to_status=new_status,
            notes=notes
        )
        self._notify_customer_status_change(new_status, cancelled_by=cancelled_by)

    
    def _notify_customer_status_change(self, new_status, cancelled_by=None):
        from .utils import notify_user

        if new_status == self.STATUS_CANCELLED:
            reason = self.cancellation_reason or 'N/A'
            if cancelled_by == self.CANCELLED_BY_VENDOR:
                notify_user(
                    self.user_profile.user,
                    "Order Cancelled by Vendor ❌",
                    f"Your order {self.order_number} was cancelled. Reason: {reason}",
                    'order_cancelled',   # ✅ string directly, no Notification.TYPE_*
                    self.id
                )
            elif cancelled_by == self.CANCELLED_BY_USER:
                notify_user(
                    self.store.shop_profile.user,
                    "Order Cancelled by Customer ❌",
                    f"Order {self.order_number} was cancelled by the customer. Reason: {reason}",
                    'order_cancelled',   # ✅
                    self.id
                )
        else:
            messages_map = {
                self.STATUS_CONFIRMED: ("Order Confirmed ✅", f"Your order {self.order_number} has been confirmed."),
                self.STATUS_PREPARING: ("Preparing Your Order 🍳", f"Order {self.order_number} is being prepared."),
                self.STATUS_READY: ("Order Ready 🎉", f"Your order {self.order_number} is ready for pickup!"),
                self.STATUS_OUT_FOR_DELIVERY: ("Out for Delivery 🚴", f"Order {self.order_number} is on its way."),
                self.STATUS_DELIVERED: ("Delivered ✅", f"Your order {self.order_number} has been delivered!"),
            }
            if new_status in messages_map:
                title, msg = messages_map[new_status]
                notify_user(
                    self.user_profile.user,
                    title,
                    msg,
                    'order_status',   # ✅
                    self.id
                )



    
   
# Add this at the bottom of your existing models.py

class ProductPayment(models.Model):

    STATUS_PENDING  = 'pending'   # ✅ ADD THIS
    STATUS_CREATED  = 'created'
    STATUS_SUCCESS  = 'success'
    STATUS_FAILED   = 'failed'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING,  'Pending'),   # ✅ ADD THIS
        (STATUS_CREATED,  'Created'),
        (STATUS_SUCCESS,  'Success'),
        (STATUS_FAILED,   'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    # ── Relations ──────────────────────────────────────────
    order = models.OneToOneField(
        ProductOrder,
        on_delete=models.CASCADE,
        related_name='payment',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='product_payments',
    )

    # ── Razorpay Fields ────────────────────────────────────
    razorpay_order_id   = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature  = models.CharField(max_length=255, blank=True, null=True)

    # ── Amount ─────────────────────────────────────────────
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paise = models.PositiveIntegerField(default=0)
    currency     = models.CharField(max_length=10, default='INR')

    # ── Status ─────────────────────────────────────────────
    status         = models.CharField(
                        max_length=20,
                        choices=STATUS_CHOICES,
                        default=STATUS_PENDING,  # ✅ default to pending
                        db_index=True
                     )
    failure_reason = models.TextField(blank=True)

    # ── Timestamps ─────────────────────────────────────────
    paid_at    = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment {self.razorpay_order_id} — ₹{self.amount} [{self.status}]"

    def mark_success(self, payment_id: str, signature: str):
        from django.utils import timezone
        self.razorpay_payment_id = payment_id
        self.razorpay_signature  = signature
        self.status              = self.STATUS_SUCCESS
        self.paid_at             = timezone.now()
        self.save(update_fields=[
            'razorpay_payment_id', 'razorpay_signature', 'status', 'paid_at'
        ])
        self.order.is_paid = True
        self.order.paid_at = timezone.now()
        self.order.save(update_fields=['is_paid', 'paid_at'])

    def mark_failed(self, reason: str = ''):
        self.status         = self.STATUS_FAILED
        self.failure_reason = reason
        self.save(update_fields=['status', 'failure_reason'])


class ProductOrderItem(models.Model):
    """Line items for products in an order."""
    order = models.ForeignKey(
        ProductOrder, 
        on_delete=models.CASCADE, 
        related_name="items"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        related_name="order_items"
    )
    
    # Snapshots (preserve data at time of order)
    product_name_snapshot = models.CharField(max_length=200)
    product_sku_snapshot = models.CharField(max_length=64, blank=True)
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    
    qty = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    special_instructions = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_order_items'
        indexes = [
            models.Index(fields=["order", "product"]),
        ]


class OrderStatusLog(models.Model):
    """
    Audit trail for all order status changes.
    Essential for tracking and disputes.
    """
    order = models.ForeignKey(
        ProductOrder, 
        on_delete=models.CASCADE, 
        related_name="status_logs"
    )
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who made the change (customer/vendor/admin)"
    )
    
    notes = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'order_status_logs'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['order', '-changed_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order.order_number}: {self.from_status} → {self.to_status}"
from django.utils import timezone



class Delivery(models.Model):
    """
    ENHANCED: Delivery tracking with comprehensive status.
    """
    order = models.OneToOneField(
        ProductOrder, 
        on_delete=models.CASCADE, 
        related_name="delivery"
    )
    
    tracking_code = models.CharField(
        max_length=50, 
        unique=True,
        db_index=True,
        help_text="e.g., TRK-20260218-001234"
    )
    
    # Delivery assignment
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="assigned_deliveries",
        limit_choices_to={"role": User.ROLE_ADMIN}
    )
    
    # Pickup details
    pickup_location = models.CharField(max_length=500, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery details
    delivery_address = models.TextField(null=True, blank=True)
    delivery_instructions = models.TextField(blank=True)
    
    # Timing
    estimated_pickup_time = models.DateTimeField(null=True, blank=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)

    
    # Proof of delivery
    delivery_photo_url = models.URLField(blank=True)
    delivery_signature = models.CharField(max_length=200, blank=True)
    received_by_name = models.CharField(max_length=200, blank=True)
    
    # Contact
    customer_phone = models.CharField(max_length=15, null=True, blank=True)

    delivery_person_phone = models.CharField(max_length=15, blank=True)
    
    # Status
    is_completed = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)
    
    # Metrics
    distance_km = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'deliveries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assigned_to', 'is_completed']),
            models.Index(fields=['tracking_code']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.tracking_code:
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            import random
            self.tracking_code = f"TRK-{timestamp}-{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Delivery {self.tracking_code} - Order {self.order.order_number}"


class DeliveryEvent(models.Model):
    """
    Real-time delivery tracking events.
    Creates a timeline of delivery progress.
    """
    STATUS_CREATED = "created"
    STATUS_ASSIGNED = "assigned"
    STATUS_PICKED_UP = "picked_up"
    STATUS_IN_TRANSIT = "in_transit"
    STATUS_AT_LOCATION = "at_location"
    STATUS_DELIVERED = "delivered"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_ASSIGNED, "Assigned to Delivery Person"),
        (STATUS_PICKED_UP, "Picked up from Store"),
        (STATUS_IN_TRANSIT, "In Transit"),
        (STATUS_AT_LOCATION, "At Delivery Location"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_FAILED, "Delivery Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    delivery = models.ForeignKey(
        Delivery, 
        on_delete=models.CASCADE, 
        related_name="events"
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, db_index=True)
    message = models.CharField(max_length=255, blank=True)
    
    # Location tracking
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'delivery_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["delivery", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]
    
    def __str__(self):
        return f"{self.delivery.tracking_code} - {self.get_status_display()}"





