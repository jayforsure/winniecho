from django.contrib import admin
from django.utils.html import format_html
import hashlib
from .models import (
    User, Member, Address, ProductCategory, Product, ProductImage,
    Cart, CartItem, Order, OrderItem, Payment, PasswordResetToken, DeliveryProof
)


# =====================
# SIMPLIFIED ADMIN - CRUD ONLY
# =====================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'role', 'phone', 'oauth_badge', 'verified_badge', 'created_at', 'is_email_verified']
    list_filter = ['role', 'is_email_verified', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'oauth_status']
    ordering = ['-created_at']
    list_editable = ['is_email_verified']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'birthday')
        }),
        ('Account Details', {
            'fields': ('role', 'password', 'is_email_verified', 'oauth_status'),
            'description': 'For Google OAuth users: Set a password here to enable admin login with email.'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def oauth_badge(self, obj):
        val = 'GOOGLE' if obj.is_oauth_user() else 'EMAIL'
        color = '#333' if obj.is_oauth_user() else '#666'
        return format_html('<span style="background:{};color:white;padding:3px 8px;">{}</span>', color, val)
    oauth_badge.short_description = 'Login Type'
    
    def verified_badge(self, obj):
        val = '✓' if obj.is_email_verified else '✗'
        color = 'green' if obj.is_email_verified else 'red'
        return format_html('<span style="color:{};font-size:16px;">{}</span>', color, val)
    verified_badge.short_description = 'Verified'
    
    def oauth_status(self, obj):
        if not obj:
            return ""
        
        if getattr(obj, 'is_oauth_user', lambda: False)():
            html = (
                '<div style="padding:10px;background:#f5f5f5;border-left:3px solid #333;">'
                '<strong>Google OAuth User</strong><br>'
                'This user logged in with Google. Password field is empty.<br>'
                '<em>To enable admin login, set a password below.</em>'
                '</div>'
            )
        else:
            html = (
                '<div style="padding:10px;background:#f5f5f5;border-left:3px solid #666;">'
                '<strong>Email/Password User</strong><br>'
                'This user registered with email and password.'
                '</div>'
            )
        return format_html("{}", html)
    oauth_status.short_description = 'Account Type'
    
    def save_model(self, request, obj, form, change):
        """Hash password when setting via admin panel"""
        if change:
            old_obj = User.objects.get(pk=obj.pk)
            if obj.password != old_obj.password:
                if obj.password and len(obj.password) != 64:
                    obj.password = hashlib.sha256(obj.password.encode()).hexdigest()
                    self.message_user(request, 'Password updated successfully.', level='success')
        else:
            if obj.password and len(obj.password) != 64:
                obj.password = hashlib.sha256(obj.password.encode()).hexdigest()
        
        super().save_model(request, obj, form, change)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'get_email', 'get_loyalty_points', 'get_total_spent', 'get_age']
    search_fields = ['user__name', 'user__email']
    readonly_fields = ['loyalty_points', 'total_spent']
    ordering = ['-total_spent']
    
    def get_name(self, obj):
        return obj.user.name
    get_name.short_description = 'Name'
    get_name.admin_order_field = 'user__name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_age(self, obj):
        age = obj.user.get_age()
        return age if age else '—'
    get_age.short_description = 'Age'
    
    def get_loyalty_points(self, obj):
        points_str = str(obj.loyalty_points)
        return format_html('<strong>{}</strong> pts', points_str)
    get_loyalty_points.short_description = 'Loyalty Points'
    
    def get_total_spent(self, obj):
        spent_str = str(obj.total_spent)
        return format_html('RM <strong>{}</strong>', spent_str)
    get_total_spent.short_description = 'Total Spent'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_name', 'label', 'city', 'state', 'country', 'default_badge']
    search_fields = ['user__name', 'city', 'state', 'country']
    list_filter = ['country', 'state', 'is_default']
    
    def get_user_name(self, obj):
        return obj.user.name
    get_user_name.short_description = 'User'
    
    def default_badge(self, obj):
        if obj.is_default:
            return format_html('<span style="color:green;">✓ Default</span>')
        return '—'
    default_badge.short_description = 'Default'


# =====================
# PRODUCT ADMIN (FIXED INLINE IMAGE CREATION)
# =====================

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'get_product_count', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']
    
    def get_product_count(self, obj):
        count = obj.get_product_count()
        return format_html('<strong>{}</strong> products', count)
    get_product_count.short_description = 'Active Products'


class ProductImageInline(admin.TabularInline):
    """✅ FIXED: Can now add images when creating product"""
    model = ProductImage
    extra = 1
    max_num = 4
    fields = ['image', 'is_primary', 'order', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.pk and obj.image:  # ✅ Check if saved
            return format_html('<img src="{}" style="max-height:100px;"/>', obj.image.url)
        return "Upload and save to see preview"
    image_preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'get_price', 'stock', 'get_status']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    list_editable = ['stock']
    ordering = ['-created_at']
    inlines = [ProductImageInline]
    
    def get_price(self, obj):
        price_str = str(obj.price)
        return format_html('RM <strong>{}</strong>', price_str)
    get_price.short_description = 'Price'
    
    def get_status(self, obj):
        status_dict = {0: 'Inactive', 1: 'Active', 2: 'Out of Stock'}
        color_dict = {0: '#999', 1: '#000', 2: '#666'}
        status_text = status_dict.get(obj.status, 'Unknown')
        color = color_dict.get(obj.status, '#999')
        return format_html('<span style="color:{}">{}</span>', color, status_text)
    get_status.short_description = 'Status'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_product_name', 'image_preview', 'is_primary', 'order']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name']
    list_editable = ['is_primary', 'order']
    readonly_fields = ['created_at']
    
    def get_product_name(self, obj):
        return obj.product.name
    get_product_name.short_description = 'Product'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:50px;"/>', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'


# =====================
# CART ADMIN
# =====================

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'get_total_price']
    can_delete = True
    
    def get_total_price(self, obj):
        total_str = str(obj.get_total_price())
        return format_html('RM {}', total_str)
    get_total_price.short_description = 'Total'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_name', 'get_item_count', 'get_cart_total', 'created_at']
    search_fields = ['user__name', 'user__email']
    readonly_fields = ['created_at']
    inlines = [CartItemInline]
    
    def get_user_name(self, obj):
        return obj.user.name
    get_user_name.short_description = 'User'
    
    def get_item_count(self, obj):
        count = obj.get_total_items()
        return format_html('<strong>{}</strong> items', count)
    get_item_count.short_description = 'Items'
    
    def get_cart_total(self, obj):
        total_str = str(obj.get_total())
        return format_html('RM <strong>{}</strong>', total_str)
    get_cart_total.short_description = 'Total'


# =====================
# ORDER ADMIN
# =====================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'quantity', 'unit_price', 'subtotal']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'get_user_name', 'get_subtotal', 'status', 'get_items', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'address__user__name', 'address__user__email']
    readonly_fields = ['order_number', 'created_at', 'subtotal', 'loyalty_points_earned', 'loyalty_points_used']
    inlines = [OrderItemInline]
    ordering = ['-created_at']
    list_editable = ['status']
    
    def get_user_name(self, obj):
        return obj.address.user.name
    get_user_name.short_description = 'Customer'
    
    def get_subtotal(self, obj):
        subtotal_str = str(obj.subtotal)
        return format_html('RM <strong>{}</strong>', subtotal_str)
    get_subtotal.short_description = 'Total'
    
    def get_items(self, obj):
        count = obj.get_total_items()
        return format_html('{} items', count)
    get_items.short_description = 'Items'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_order_number', 'product_name', 'quantity', 'get_unit_price', 'get_subtotal']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['order__order_number', 'product_name']
    readonly_fields = ['order', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal']
    
    def get_order_number(self, obj):
        return obj.order.order_number
    get_order_number.short_description = 'Order'
    
    def get_unit_price(self, obj):
        price_str = str(obj.unit_price)
        return format_html('RM {}', price_str)
    get_unit_price.short_description = 'Unit Price'
    
    def get_subtotal(self, obj):
        subtotal_str = str(obj.subtotal)
        return format_html('RM <strong>{}</strong>', subtotal_str)
    get_subtotal.short_description = 'Subtotal'


# =====================
# PAYMENT ADMIN
# =====================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_order_number', 'get_customer', 'get_amount', 'method', 'status', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['order__order_number', 'order__address__user__name', 'transaction_id']
    readonly_fields = ['created_at', 'total_amount', 'discount_amount', 'transaction_id']
    ordering = ['-created_at']
    
    def get_order_number(self, obj):
        return obj.order.order_number
    get_order_number.short_description = 'Order'
    
    def get_customer(self, obj):
        return obj.order.address.user.name
    get_customer.short_description = 'Customer'
    
    def get_amount(self, obj):
        amount_str = str(obj.total_amount)
        return format_html('RM <strong>{}</strong>', amount_str)
    get_amount.short_description = 'Amount'
    
    actions = ['mark_as_success', 'mark_as_failed']
    
    def mark_as_success(self, request, queryset):
        for payment in queryset:
            payment.mark_as_paid()
        self.message_user(request, f'{queryset.count()} payments marked as successful.')
    mark_as_success.short_description = 'Mark as Success'
    
    def mark_as_failed(self, request, queryset):
        queryset.update(status='F')
        self.message_user(request, f'{queryset.count()} payments marked as failed.')
    mark_as_failed.short_description = 'Mark as Failed'


# =====================
# PASSWORD RESET TOKEN
# =====================

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_name', 'is_valid_badge', 'created_at', 'used_at']
    list_filter = ['created_at', 'used_at']
    search_fields = ['user__name', 'user__email', 'token']
    readonly_fields = ['created_at', 'used_at', 'token']
    ordering = ['-created_at']
    
    def get_user_name(self, obj):
        return obj.user.name
    get_user_name.short_description = 'User'
    
    def is_valid_badge(self, obj):
        if obj.is_valid():
            return format_html('<span style="color:green;">✓ Valid</span>')
        return format_html('<span style="color:red;">✗ Expired</span>')
    is_valid_badge.short_description = 'Status'


@admin.register(DeliveryProof)
class DeliveryProofAdmin(admin.ModelAdmin):
    list_display = ['order', 'driver', 'uploaded_at', 'image_preview']
    list_filter = ['uploaded_at']
    search_fields = ['order__order_number', 'driver__name']
    readonly_fields = ['uploaded_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:100px; border:1px solid #ddd;"/>', 
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


# =====================
# ADMIN SITE CUSTOMIZATION
# =====================

admin.site.site_header = "WinnieChO Admin Panel"
admin.site.site_title = "WinnieChO Admin"
admin.site.index_title = "Administration"

# Add link to analytics dashboard in admin index
from django.urls import reverse
from django.utils.html import format_html

# Override admin index template context
original_index = admin.site.index

def custom_index(request, extra_context=None):
    extra_context = extra_context or {}
    extra_context['analytics_url'] = '/secure/admin/analytics/'
    return original_index(request, extra_context)

admin.site.index = custom_index