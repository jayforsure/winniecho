from django.contrib import admin
from django.utils.html import format_html
from .models import (
    User, Member, Address, ProductCategory, Product, ProductImage,
    Cart, CartItem, Order, OrderItem, Payment, PasswordResetToken
)


# =====================
# USER & MEMBER ADMIN
# =====================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'role', 'phone', 'is_email_verified', 'created_at']
    list_filter = ['role', 'is_email_verified', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_editable = ['is_email_verified']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'birthday')
        }),
        ('Account Details', {
            'fields': ('role', 'password', 'is_email_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'get_email', 'loyalty_points', 'total_spent', 'get_age']
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
        return obj.user.get_age()
    get_age.short_description = 'Age'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_name', 'city', 'state', 'country']
    search_fields = ['user__name', 'city', 'state', 'country']
    list_filter = ['country', 'state']
    
    def get_user_name(self, obj):
        return obj.user.name
    get_user_name.short_description = 'User'
    get_user_name.admin_order_field = 'user__name'


# =====================
# PRODUCT ADMIN
# =====================

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'get_product_count', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']
    
    def get_product_count(self, obj):
        return obj.get_product_count()
    get_product_count.short_description = 'Active Products'


# Product Image Inline for uploading multiple images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 4  # Maximum 4 images per product
    fields = ['image', 'is_primary', 'order', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 5px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category', 'price', 'stock', 'status',
        'status_badge', 'stock_status', 'image_count', 'created_at'
    ]
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'image_count']
    list_editable = ['price', 'stock', 'status']
    ordering = ['-created_at']
    inlines = [ProductImageInline]  # Add inline for images
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'short_description', 'description')
        }),
        ('Categorization', {
            'fields': ('category',)
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock')
        }),
        ('Product Details', {
            'fields': ('ingredients',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Images', {
            'fields': ('image_count',),
            'description': 'Use the Product Images section below to upload images (max 4)'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def image_count(self, obj):
        count = obj.images.count()
        if count == 0:
            return format_html('<span style="color: red;">⚠ No images</span>')
        elif count < 4:
            return format_html('<span style="color: orange;">{} image(s)</span>', count)
        return format_html('<span style="color: green;">✓ {} images</span>', count)
    image_count.short_description = 'Images'
    
    def status_badge(self, obj):
        colors = {
            0: 'gray',
            1: 'green',
            2: 'red'
        }
        labels = {
            0: 'Inactive',
            1: 'Active',
            2: 'Out of Stock'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            labels.get(obj.status, 'Unknown')
        )
    status_badge.short_description = 'Status'
    
    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: red;">⚠ Out of Stock</span>')
        elif obj.is_low_stock():
            return format_html('<span style="color: orange;">⚠ Low Stock</span>')
        return format_html('<span style="color: green;">✓ In Stock</span>')
    stock_status.short_description = 'Stock Status'
    
    actions = ['mark_as_active', 'mark_as_inactive', 'mark_as_out_of_stock']
    
    def mark_as_active(self, request, queryset):
        queryset.update(status=1)
        self.message_user(request, f'{queryset.count()} products marked as active.')
    mark_as_active.short_description = 'Mark selected as Active'
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(status=0)
        self.message_user(request, f'{queryset.count()} products marked as inactive.')
    mark_as_inactive.short_description = 'Mark selected as Inactive'
    
    def mark_as_out_of_stock(self, request, queryset):
        queryset.update(status=2)
        self.message_user(request, f'{queryset.count()} products marked as out of stock.')
    mark_as_out_of_stock.short_description = 'Mark selected as Out of Stock'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_product_name', 'image_preview', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name']
    list_editable = ['is_primary', 'order']
    readonly_fields = ['created_at', 'image_preview_large']
    ordering = ['product', '-is_primary', 'order']
    
    def get_product_name(self, obj):
        return obj.product.name
    get_product_name.short_description = 'Product'
    get_product_name.admin_order_field = 'product__name'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 5px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 300px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return "No image"
    image_preview_large.short_description = 'Image Preview'


# =====================
# CART ADMIN
# =====================

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'get_total_price']
    can_delete = True
    
    def get_total_price(self, obj):
        return f"RM {obj.get_total_price()}"
    get_total_price.short_description = 'Total'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_name', 'get_total_items', 'get_total', 'created_at']
    search_fields = ['user__name', 'user__email']
    readonly_fields = ['created_at', 'get_total_items', 'get_total']
    inlines = [CartItemInline]
    
    def get_user_name(self, obj):
        return obj.user.name
    get_user_name.short_description = 'User'
    get_user_name.admin_order_field = 'user__name'
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'
    
    def get_total(self, obj):
        return f"RM {obj.get_total()}"
    get_total.short_description = 'Cart Total'


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
    list_display = [
        'order_number', 'get_user_name', 'subtotal', 'status', 'status_badge',
        'get_total_items', 'loyalty_points_earned', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'address__user__name', 'address__user__email']
    readonly_fields = [
        'order_number', 'created_at', 'subtotal', 'loyalty_points_earned', 
        'loyalty_points_used', 'get_total_items'
    ]
    inlines = [OrderItemInline]
    ordering = ['-created_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'address', 'status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'loyalty_points_used', 'loyalty_points_earned')
        }),
        ('Details', {
            'fields': ('get_total_items',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def get_user_name(self, obj):
        return obj.address.user.name
    get_user_name.short_description = 'Customer'
    get_user_name.admin_order_field = 'address__user__name'
    
    def status_badge(self, obj):
        colors = {
            'P': 'orange',
            'C': 'blue',
            'S': 'purple',
            'D': 'green',
            'X': 'red'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'
    
    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='C')
        self.message_user(request, f'{queryset.count()} orders marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark as Confirmed'
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='S')
        self.message_user(request, f'{queryset.count()} orders marked as shipped.')
    mark_as_shipped.short_description = 'Mark as Shipped'
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='D')
        self.message_user(request, f'{queryset.count()} orders marked as delivered.')
    mark_as_delivered.short_description = 'Mark as Delivered'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_order_number', 'product_name', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['order__order_number', 'order__address__user__name', 'product__name', 'product_name']
    readonly_fields = ['order', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal']
    
    def get_order_number(self, obj):
        return obj.order.order_number
    get_order_number.short_description = 'Order'
    get_order_number.admin_order_field = 'order__order_number'


# =====================
# PAYMENT ADMIN
# =====================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_order_number', 'get_customer', 'total_amount',
        'method_badge', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['order__order_number', 'order__address__user__name', 'order__address__user__email', 'transaction_id']
    readonly_fields = ['created_at', 'total_amount', 'discount_amount', 'transaction_id']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'method', 'status', 'transaction_id')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'discount_amount')
        }),
        ('Additional Details', {
            'fields': ('payment_details',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def get_order_number(self, obj):
        return obj.order.order_number
    get_order_number.short_description = 'Order'
    get_order_number.admin_order_field = 'order__order_number'
    
    def get_customer(self, obj):
        return obj.order.address.user.name
    get_customer.short_description = 'Customer'
    
    def method_badge(self, obj):
        colors = {
            'PP': 'blue',
            'ST': 'purple',
            'COD': 'orange'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.method, 'gray'),
            obj.get_method_display()
        )
    method_badge.short_description = 'Method'
    
    def status_badge(self, obj):
        colors = {
            'P': 'orange',
            'S': 'green',
            'F': 'red',
            'C': 'gray'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
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
    list_display = ['id', 'get_user_name', 'is_valid_status', 'created_at', 'used_at']
    list_filter = ['created_at', 'used_at']
    search_fields = ['user__name', 'user__email', 'token']
    readonly_fields = ['created_at', 'used_at', 'is_valid_status', 'token']
    ordering = ['-created_at']
    
    def get_user_name(self, obj):
        return obj.user.name
    get_user_name.short_description = 'User'
    get_user_name.admin_order_field = 'user__name'
    
    def is_valid_status(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid/Expired</span>')
    is_valid_status.short_description = 'Status'


# Customize admin site header
admin.site.site_header = "WinnieCho Admin"
admin.site.site_title = "WinnieCho Admin Portal"
admin.site.index_title = "Welcome to WinnieCho Administration"