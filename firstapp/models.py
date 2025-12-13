# UPDATED MODELS.PY - Multiple Addresses + Improvements

import os
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, date
from django.conf import settings
from decimal import Decimal
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# -----------------------
# User (Base User Model)
# -----------------------
class User(models.Model):
    """
    Base user model for both members and guests
    """
    type_choices = [
        ('M', 'Member'),
        ('A', 'Admin'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True, db_index=True)
    password = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    birthday = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=1, choices=type_choices, db_index=True, default='M')
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']), 
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"
    
    def is_member(self):
        """Check if user is a member"""
        return self.role == 'M'
    
    def get_age(self):
        """Calculate member's age"""
        if not self.birthday:
            return None
        today = date.today()
        return today.year - self.birthday.year - (
            (today.month, today.day) < (self.birthday.month, self.birthday.day)
        )
    
    def is_admin(self):
        """Check if member is admin"""
        return self.role == 'A'
    
    def get_default_address(self):
        """Get user's default address"""
        return self.addresses.filter(is_default=True).first() or self.addresses.first()
    
    def send_verification_email(self, token):
        """Send email verification"""
        subject = 'Verify Your Email - WinnieCho'
        verification_url = f"{settings.SITE_URL}/verify-email/{token}/"
        html_message = render_to_string('emails/email_verification.html', {
            'user': self,
            'verification_url': verification_url
        })
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [self.email], html_message=html_message)


# -----------------------
# Email Verification Token
# -----------------------
class EmailVerificationToken(models.Model):
    """
    Token for email verification
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=200, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'email_verification_token'
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Verification token for {self.user.email}"
    
    def is_valid(self):
        """Check if token is still valid (24 hours)"""
        if self.used_at:
            return False
        expiry = self.created_at + timedelta(hours=24)
        return timezone.now() < expiry
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used_at = timezone.now()
        self.save()


# -----------------------
# Address (UPDATED - Multiple Addresses)
# -----------------------
class Address(models.Model):
    """
    Addresses for users (multiple addresses allowed)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, default='Home')  # Home, Work, etc.
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Malaysia')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'address'
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.user.name}'s {self.label} Address"

    def get_full_address(self):
        """Get formatted full address"""
        parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ", ".join(filter(None, parts))
    
    def save(self, *args, **kwargs):
        # If this is set as default, remove default from others
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        # If this is the first address, make it default
        if not self.pk and not Address.objects.filter(user=self.user).exists():
            self.is_default = True
        super().save(*args, **kwargs)


# -----------------------
# Member (Extends User)
# -----------------------
class Member(models.Model):
    """
    Member profile with authentication and loyalty features
    UPDATED LOYALTY LOGIC:
    - Earn: RM 1 spent = 0.01 points
    - Redeem: 1 point = RM 0.5 discount
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='member_profile')
    loyalty_points = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'member'
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        ordering = ['-user__created_at']

    def __str__(self):
        return f"{self.user.name} - Points: {self.loyalty_points}"
    
    def add_loyalty_points(self, amount_spent):
        """
        Add loyalty points based on spending
        UPDATED RULE: Spend RM 1 = 0.01 points
        """
        points_earned = Decimal(str(amount_spent)) / Decimal('100')
        self.loyalty_points += points_earned
        self.total_spent += Decimal(str(amount_spent))
        self.save()
        return points_earned

    def redeem_points(self, points_to_redeem):
        """
        Redeem loyalty points
        UPDATED RULE: 1 point = RM 0.5 discount
        """
        points_to_redeem = Decimal(str(points_to_redeem))
        if points_to_redeem > self.loyalty_points:
            raise ValidationError("Insufficient loyalty points")
        
        self.loyalty_points -= points_to_redeem
        self.save()
        
        # Return discount amount: 1 point = RM 0.5
        discount_amount = points_to_redeem * Decimal('0.5')
        return discount_amount
    
    def get_points_value(self):
        """Get monetary value of loyalty points"""
        return self.loyalty_points * Decimal('0.5')
    
    def calculate_points_from_spending(self, amount):
        """Calculate how many points user will earn"""
        return Decimal(str(amount)) / Decimal('100')
    
    def calculate_discount_from_points(self, points):
        """Calculate discount amount from points"""
        return Decimal(str(points)) * Decimal('0.5')


# -----------------------
# Product Category
# -----------------------
class ProductCategory(models.Model):
    """
    Categories for chocolate products
    """
    category_choices = [
        ('D', 'Dark Chocolate'),
        ('M', 'Milk Chocolate'),
        ('W', 'White Chocolate'),
        ('A', 'Alcohol Chocolate'),
    ]

    code = models.CharField(max_length=1, unique=True, choices=category_choices)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_category'
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def get_product_count(self):
        """Get number of active products in this category"""
        return self.products.filter(status=1).count()


# -----------------------
# Product
# -----------------------
class Product(models.Model):
    """
    Chocolate products available for purchase
    """
    status_choices = [
        (0, 'Inactive'),
        (1, 'Active'),
        (2, 'Out of Stock'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.RESTRICT, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    ingredients = models.TextField(blank=True)
    status = models.IntegerField(choices=status_choices, default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return f"{self.name} (RM {self.price})"
    
    def is_available(self):
        """Check if product is available for purchase"""
        return self.status == 1 and self.stock > 0
    
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.stock <= 10
    
    def reduce_stock(self, quantity):
        """Reduce stock and update status if needed"""
        if self.stock >= quantity:
            self.stock -= quantity
            if self.stock == 0:
                self.status = 2  # Out of Stock
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity):
        """Increase stock and update status"""
        self.stock += quantity
        if self.status == 2 and self.stock > 0:
            self.status = 1  # Active
        self.save()
    
    def get_primary_image(self):
        """Get the primary product image"""
        images = self.images.filter(is_primary=True).first()
        if not images:
            images = self.images.first()
        return images
    
    def get_all_images(self):
        """Get all product images"""
        return self.images.all().order_by('-is_primary', 'order')


# -----------------------
# Product Image
# -----------------------
class ProductImage(models.Model):
    """
    Multiple images for each product (max 4)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_image'
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['-is_primary', 'order']

    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, remove primary from others
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def clean(self):
        # Validate max 4 images per product
        if not self.pk:  # Only check on creation
            count = ProductImage.objects.filter(product=self.product).count()
            if count >= 4:
                raise ValidationError("Maximum 4 images per product allowed")


# -----------------------
# Cart
# -----------------------
class Cart(models.Model):
    """
    Shopping cart for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart'
        verbose_name = 'Shopping Cart'
        verbose_name_plural = 'Shopping Carts'

    def __str__(self):
        return f"Cart for {self.user.name}"
    
    def get_total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    def get_subtotal(self):
        """Get cart subtotal"""
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_total(self):
        """Get cart total (same as subtotal, discount handled at checkout)"""
        return self.get_subtotal()
    
    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()
    
    def is_empty(self):
        """Check if cart is empty"""
        return self.items.count() == 0


# -----------------------
# Cart Item
# -----------------------
class CartItem(models.Model):
    """
    Individual items in shopping cart
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_item'
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = [['cart', 'product']]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    def get_unit_price(self):
        """Get unit price"""
        return self.product.price
    
    def get_total_price(self):
        """Get total price for this cart item"""
        return self.get_unit_price() * self.quantity
    
    def clean(self):
        """Validate cart item"""
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        
        if self.quantity > self.product.stock:
            raise ValidationError(f"Only {self.product.stock} items available in stock")


# -----------------------
# Order
# -----------------------
class Order(models.Model):
    """
    Customer orders
    """
    status_choices = [
        ('P', 'Pending'),
        ('C', 'Confirmed'),
        ('S', 'Shipped'),
        ('D', 'Delivered'),
        ('X', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='orders')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=1, choices=status_choices, default='P', db_index=True)
    loyalty_points_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    loyalty_points_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['address', 'status']),
        ]

    def __str__(self):
        return f"Order {self.order_number} - {self.address.user.name}"
    
    def generate_order_number(self):
        """Generate unique order number"""
        from datetime import datetime
        import random
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_num = random.randint(1000, 9999)
        return f"CHO{timestamp}{random_num}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # If this is a new order with loyalty points used, deduct them
        if not self.pk and hasattr(self, '_loyalty_points_to_use') and self._loyalty_points_to_use > 0:
            if self.address.user.is_member():
                try:
                    member = self.address.user.member_profile
                    discount_amount = member.redeem_points(self._loyalty_points_to_use)
                    self.loyalty_points_used = self._loyalty_points_to_use
                    # discount_amount will be used in payment
                except Exception as e:
                    # Handle error - maybe set points_used to 0
                    self.loyalty_points_used = 0
                    print(f"Error redeeming points: {e}")
        super().save(*args, **kwargs)
    
    def get_total_items(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items.all())
    
    def send_confirmation_email(self):
        """Send order confirmation email"""
        payment = self.payments.first()
        subject = f'Order Confirmation #{self.order_number} - WinnieCho'
        html_message = render_to_string('emails/order_confirmation.html', {
            'order': self,
            'payment': payment,
            'items': self.items.all()
        })
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, 
                 [self.address.user.email], html_message=html_message)


# -----------------------
# Order Item
# -----------------------
class OrderItem(models.Model):
    """
    Individual items in an order
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_item'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
    
    def save(self, *args, **kwargs):
        """Calculate total price before saving"""
        self.subtotal = self.unit_price * self.quantity
        if not self.product_name:
            self.product_name = self.product.name
        super().save(*args, **kwargs)


# -----------------------
# Payment
# -----------------------
class Payment(models.Model):
    """
    Payment records for orders
    """
    method_choices = [
        ('PP', 'PayPal'),
        ('ST', 'Stripe'),
        ('COD', 'Cash on Delivery'),
    ]

    status_choices = [
        ('P', 'Pending'),
        ('S', 'Success'),
        ('F', 'Failed'),
        ('C', 'Cancelled'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=3, choices=method_choices)
    status = models.CharField(max_length=1, choices=status_choices, default='P')
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment for Order {self.order.order_number} - RM{self.total_amount}"
    
    def mark_as_paid(self):
        """Mark payment as successful"""
        self.status = 'S'
        self.save()
        
        if self.order.address.user.is_member():
            try:
                member = self.order.address.user.member_profile
                
                # 1. Deduct points that were used (if any)
                if self.order.loyalty_points_used > 0:
                    # Points should already be deducted when order was created,
                    current_points = member.loyalty_points
                    # Points are deducted in the Order.save() method above
                
                # 2. Add points earned from this purchase (after discount)
                # Earn points based on actual amount paid (total_amount)
                points_earned = member.add_loyalty_points(self.total_amount)
                self.order.loyalty_points_earned = points_earned
                self.order.save()
                
                print(f"✅ Member loyalty updated: Used {self.order.loyalty_points_used} points, Earned {points_earned} points")
                print(f"✅ Current points: {current_points}")
                
            except Exception as e:
                print(f"Error updating loyalty: {e}")

            # Send confirmation email
            self.order.send_confirmation_email()


# -----------------------
# Password Reset Token
# -----------------------
class PasswordResetToken(models.Model):
    """
    Token for password reset functionality
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=200, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'password_reset_token'
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    def is_valid(self):
        """Check if token is still valid (30 minutes)"""
        if self.used_at:
            return False
        expiry = self.created_at + timedelta(minutes=30)
        return timezone.now() < expiry
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used_at = timezone.now()
        self.save()
    
    def send_reset_email(self):
        """Send password reset email"""
        subject = 'Reset Your Password - WinnieCho'
        reset_url = f"{settings.SITE_URL}/reset-password/{self.token}/"
        html_message = render_to_string('emails/password_reset.html', {
            'user': self.user,
            'reset_url': reset_url
        })
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, 
                 [self.user.email], html_message=html_message)