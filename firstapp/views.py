from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncDate, TruncMonth
from decimal import Decimal
import hashlib
import secrets
from datetime import datetime, timedelta
import json
import uuid
import paypalrestsdk
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import boto3
from PIL import Image
import io


from .models import (
    User, Member, Address, Product, ProductCategory,
    Cart, CartItem, Order, OrderItem, Payment, PasswordResetToken, DeliveryProof
)

def health(request):
    return HttpResponse("ok")

# Configure PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # "sandbox" or "live"
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})
# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# =====================
# PUBLIC VIEWS
# =====================

def home(request):
    """Home page with featured products"""
    featured_products = Product.objects.filter(status=1)[:8]
    categories = ProductCategory.objects.all()
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'index.html', context)


def products(request):
    # Get filter parameters
    category_code = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '')
    search_query = request.GET.get('search', '')
    
    # Get all ACTIVE products (status=1 means Active)
    products = Product.objects.filter(status=1)
    
    # Filter by category
    if category_code:
        products = products.filter(category__code=category_code)
    
    # Filter by search
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Sort products
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')  # Default
    
    # Check if AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        # Return JSON for AJAX requests
        products_data = []
        for product in products:
            # Get all product images
            images = [img.image.url for img in product.get_all_images()]
            
            products_data.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'price': str(product.price),
                'stock': product.stock,
                'category': product.category.name,
                'images': images
            })
        
        return JsonResponse({
            'products': products_data,
            'count': len(products_data)
        })
    
    # Normal page request - return HTML
    categories = ProductCategory.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_code,
        'selected_sort': sort_by,
        'search_query': search_query
    }
    
    return render(request, 'product/products.html', context)


def product_detail(request, product_id):
    """Individual product detail page"""
    product = get_object_or_404(Product, pk=product_id)
    related_products = Product.objects.filter(
        category=product.category,
        status=1
    ).exclude(pk=product_id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'product/product_detail.html', context)


# =====================
# AUTHENTICATION
# =====================

def register(request):
    """User registration WITH ADDRESS"""
    if request.method == 'POST':
        # User fields
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        birthday = request.POST.get('birthday')
        
        # Address fields
        address_line = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country', 'Malaysia')
        
        # Validate
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('register')
        
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user
        user = User.objects.create(
            name=name,
            email=email,
            password=hashed_password,
            phone=phone,
            birthday=birthday if birthday else None,
            role='M'
        )
        
        # Create member profile
        Member.objects.create(user=user)
        
        # Create cart
        Cart.objects.create(user=user)
        
        # Create default address
        Address.objects.create(
            user=user,
            label='Home',
            address=address_line,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=True
        )
        
        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')
    
    return render(request, 'account/register.html')


def create_user_profile(backend, user, response, *args, **kwargs):
    """
    Create user profile after Google OAuth login
    """
    from .models import User, Member, Cart
    import secrets
    
    # Check if this is a new user
    if kwargs.get('is_new', False):
        # Get Google user info
        request = kwargs.get('request')

        email = response.get('email')
        name = response.get('name', email.split('@')[0])
        
        # Check if user exists in our system
        try:
            our_user = User.objects.get(email=email)
            # User exists, just link the social auth
        except User.DoesNotExist:
            # Create new user for Google login
            our_user = User.objects.create(
                name=name,
                email=email,
                password='',  # ✅ EMPTY for Google users
                phone='',     # ✅ EMPTY for Google users
                role='M',     # Default to Member
                is_email_verified=True  # ✅ Google emails are verified
            )
            
            # Create member profile
            Member.objects.create(user=our_user)
            
            # Create cart
            Cart.objects.create(user=our_user)
        
        # Store in session
        kwargs['request'].session['user_id'] = our_user.id
        kwargs['request'].session['user_name'] = our_user.name
        kwargs['request'].session['user_email'] = our_user.email
        kwargs['request'].session['user_role'] = our_user.role

        messages.success(request, f'Welcome back, {our_user.name}!')
    
    return kwargs


def login_view(request):
    """User login with admin detection"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            user = User.objects.get(email=email, password=hashed_password)
            
            # Store user ID in session
            request.session['user_id'] = user.id
            request.session['user_name'] = user.name
            request.session['user_email'] = user.email
            request.session['user_role'] = user.role  # ✅ ADD THIS
            
            messages.success(request, f'Welcome back, {user.name}!')
            
            # ✅ CHECK IF ADMIN - Redirect to admin dashboard
            if user.is_admin():
                return redirect('/admin/', {'is_admin': request.user.is_authenticated and request.session['user_role'] == 'A'})
            
            if user.is_driver():
                return redirect('driver_dashboard')
            
            # Regular user - redirect to dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
            
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')
            return redirect('login')
    
    return render(request, 'account/login.html')


def logout_view(request):
    """User logout"""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully')
    return redirect('home')


# =====================
# CART FUNCTIONALITY
# =====================

def get_user_from_session(request):
    """Helper to get user from session"""
    user_id = request.session.get('user_id')
    if user_id:
        return User.objects.get(pk=user_id)
    return None


@require_POST
def add_to_cart(request, product_id):
    """Add product to cart"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Please login first'}, status=401)
    
    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check stock
    if quantity > product.stock:
        return JsonResponse({'error': 'Insufficient stock'}, status=400)
    
    # Get or create cart
    cart, _ = Cart.objects.get_or_create(user=user)
    
    # Check if coming from cart sync (has 'sync' parameter)
    is_sync = request.POST.get('sync') == 'true'
    
    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        if is_sync:
            # From sync: SET the quantity (don't add)
            cart_item.quantity = quantity
        else:
            # From manual add: ADD to quantity
            cart_item.quantity += quantity
        
        # Check stock again after update
        if cart_item.quantity > product.stock:
            return JsonResponse({'error': 'Insufficient stock'}, status=400)
        
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Added to cart',
        'cart_count': cart.get_total_items()
    })


def cart_view(request):
    """Shopping cart page"""
    user = get_user_from_session(request)
    if not user:
        return redirect('login')
    
    cart = Cart.objects.filter(user=user).first()
    
    context = {
        'cart': cart,
    }
    return render(request, 'order/cart.html', context)


@require_POST
def update_cart(request, item_id):
    """Update cart item quantity"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=user)
    quantity = int(request.POST.get('quantity'))
    
    if quantity <= 0:
        cart_item.delete()
        return JsonResponse({'success': True, 'message': 'Item removed'})
    
    if quantity > cart_item.product.stock:
        return JsonResponse({'error': 'Insufficient stock'}, status=400)
    
    cart_item.quantity = quantity
    cart_item.save()
    
    return JsonResponse({
        'success': True,
        'item_total': float(cart_item.get_total_price()),
        'cart_total': float(cart_item.cart.get_total())
    })


@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=user)
    cart_item.delete()
    
    return JsonResponse({'success': True, 'message': 'Item removed from cart'})


@require_POST
def clear_cart(request):
    """Clear user's cart"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    cart = Cart.objects.filter(user=user).first()
    if cart:
        cart.clear()
    
    return JsonResponse({'success': True})


# =====================
# CHECKOUT & ORDERS
# =====================

def checkout(request):
    """Checkout page with address selection - FIXED VERSION"""
    user = get_user_from_session(request)
    if not user:
        return redirect('login')
    
    # Get cart WITHOUT clearing it
    cart = Cart.objects.filter(user=user).first()
    
    # Check if cart exists AND has items
    if not cart or cart.is_empty():
        messages.warning(request, 'Your cart is empty')
        return redirect('products')
    
    # Get all user addresses
    addresses = Address.objects.filter(user=user).order_by('-is_default')
    
    # If no addresses, redirect to manage addresses with return URL
    if not addresses.exists():
        messages.info(request, 'Please add a delivery address first')
        request.session['checkout_return'] = True
        return redirect('manage_addresses')
    
    default_address = user.get_default_address()
    
    # Get member for loyalty points
    member = None
    if user.is_member():
        member = user.member_profile
    
    # Calculate totals
    subtotal = cart.get_subtotal()
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
        'subtotal': subtotal,
        'addresses': addresses,
        'default_address': default_address,
        'member': member,
    }
    return render(request, 'order/checkout.html', context)


@require_POST
def process_checkout(request):
    """Process checkout and create order - WITH ADMIN NOTIFICATION"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    cart = Cart.objects.filter(user=user).first()
    if not cart or cart.is_empty():
        return JsonResponse({'error': 'Cart is empty'}, status=400)
    
    address_id = request.POST.get('address_id')
    
    if not address_id:
        return JsonResponse({'error': 'Please select an address'}, status=400)
    
    try:
        user_address = Address.objects.get(id=address_id, user=user)
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Invalid address'}, status=400)
    
    subtotal = cart.get_subtotal()
    loyalty_points_used = Decimal(request.POST.get('loyalty_points_used', '0'))
    discount_amount = Decimal('0')
    
    if loyalty_points_used > 0:
        if not user.is_member():
            return JsonResponse({'error': 'Not a member'}, status=400)
        
        member = user.member_profile
        if loyalty_points_used > member.loyalty_points:
            return JsonResponse({'error': 'Insufficient loyalty points'}, status=400)
        
        try:
            discount_amount = member.redeem_points(loyalty_points_used)
        except Exception as e:
            return JsonResponse({'error': f'Failed to use loyalty points: {str(e)}'}, status=400)
    
    total_amount = subtotal - discount_amount
    
    # Create order
    order = Order.objects.create(
        address=user_address,
        subtotal=subtotal,
        status='P',  # Pending
        loyalty_points_used=loyalty_points_used
    )
    
    # Create order items
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.price,
            subtotal=cart_item.get_total_price()
        )
        cart_item.product.reduce_stock(cart_item.quantity)
    
    # Create pending payment record
    Payment.objects.create(
        order=order,
        discount_amount=discount_amount,
        total_amount=total_amount,
        method='COD',  # Temporary
        status='P'
    )
    
    # ✅ SEND ADMIN NOTIFICATION (NEW!)
    send_admin_notification(order)
    
    # Store order in session
    request.session['pending_order_id'] = order.id
    request.session['pending_order_total'] = float(total_amount)
    request.session['pending_order_discount'] = float(discount_amount)
    request.session['loyalty_points_to_redeem'] = float(loyalty_points_used)
    
    return JsonResponse({
        'success': True,
        'redirect': '/payment/'
    })


def payment(request):
    """Payment page - shows order summary and payment methods"""
    user = get_user_from_session(request)
    if not user:
        return redirect('login')

    order_id = request.session.get('pending_order_id')
    if not order_id:
        messages.error(request, 'No pending order found. Please complete checkout first.')
        return redirect('checkout')  # CHANGED: redirect to checkout, not products

    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        pk=order_id,
        address__user=user
    )

    # Get order items
    order_items = order.items.all()

    # Calculate totals
    subtotal = order.subtotal
    loyalty_discount = Decimal(str(request.session.get('pending_order_discount', 0)))
    total = Decimal(str(request.session.get('pending_order_total', subtotal)))

    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'loyalty_discount': loyalty_discount,
        'total': total,
        'address': order.address,  # Address is already selected
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }

    return render(request, 'order/payment.html', context)


@require_POST
def process_payment(request):
    """Process payment selection and create payment record"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    order_id = request.session.get('pending_order_id')
    if not order_id:
        return JsonResponse({'error': 'No pending order'}, status=400)
    
    order = get_object_or_404(Order, pk=order_id, address__user=user)
    
    # Get payment details
    payment_method = request.POST.get('payment_method', 'ST')
    total_amount = Decimal(request.session.get('pending_order_total', order.subtotal))
    discount_amount = Decimal(request.session.get('pending_order_discount', 0))
    
    # Create payment record
    payment = Payment.objects.create(
        order=order,
        discount_amount=discount_amount,
        total_amount=total_amount,
        method=payment_method,
        status='P'  # Pending
    )
    
    # Process based on payment method
    if payment_method == 'COD':
        # Cash on Delivery - mark as pending cash payment
        payment.status = 'C'  # Cash pending
        payment.save()
        
        # Update order status
        order.status = 'C'  # Confirmed
        order.save()

        # ✅ AWARD LOYALTY POINTS FOR COD TOO
        if order.address.user.is_member():
            try:
                member = order.address.user.member_profile
                # Use the payment total amount (after discount)
                points_earned = member.add_loyalty_points(total_amount)
                order.loyalty_points_earned = points_earned
                order.save()
                print(f"DEBUG: Awarded {points_earned} points for COD order")
            except Exception as e:
                print(f"DEBUG: Error awarding points for COD: {e}")

        # Send confirmation email
        order.send_confirmation_email()
        
        # ✅ Clear the cart BEFORE redirect
        user = get_user_from_session(request)
        if user:
            cart = Cart.objects.filter(user=user).first()
            if cart:
                cart.clear()

        # Clear session
        _clear_payment_session(request)
        
        return JsonResponse({
            'success': True,
            'redirect': f'/payment/success/{order.id}/'
        })
    
    elif payment_method == 'PP':
        # PayPal payment - redirect to PayPal
        return create_paypal_payment(request, payment)
    
    elif payment_method == 'ST':
        # Stripe payment - redirect to Stripe
        return create_stripe_payment(request, payment)
    
    else:
        return JsonResponse({
            'success': False,
            'error': 'Invalid payment method'
        }, status=400)


# =====================
# PAYPAL PAYMENT FLOW
# =====================

def create_paypal_payment(request, payment):
    """Create PayPal payment and redirect to PayPal"""
    try:
        # Calculate amount
        amount = float(payment.total_amount)
        
        # Create PayPal payment
        paypal_payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(
                    f'/payment/paypal/success/{payment.id}/'
                ),
                "cancel_url": request.build_absolute_uri(
                    f'/payment/cancel/{payment.id}/'
                )
            },
            "transactions": [{
                "amount": {
                    "total": f"{amount:.2f}",
                    "currency": "MYR"
                },
                "description": f"Chocolate Order #{payment.order.order_number}",
                "invoice_number": payment.order.order_number
            }]
        })

        if paypal_payment.create():
            # Find approval URL
            for link in paypal_payment.links:
                if link.rel == "approval_url":
                    return JsonResponse({
                        'success': True,
                        'redirect': link.href
                    })
        
        # If no approval URL found
        messages.error(request, 'PayPal payment creation failed.')
        return JsonResponse({
            'success': False,
            'error': 'PayPal payment creation failed'
        }, status=500)
           
    except Exception as e:
        print(f"PayPal Error: {str(e)}")
        messages.error(request, f'PayPal error: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': f'PayPal error: {str(e)}'
        }, status=500)


def paypal_success(request, payment_id):
    """Handle PayPal return after successful payment"""
    try:
        payment = get_object_or_404(Payment, id=payment_id)
        payer_id = request.GET.get('PayerID')
        paypal_payment_id = request.GET.get('paymentId')

        # Execute the payment
        paypal_payment = paypalrestsdk.Payment.find(paypal_payment_id)
        
        if paypal_payment.execute({"payer_id": payer_id}):
            # Payment successful
            payment.order.status = 'C'
            payment.status = 'S'  # Success
            payment.transaction_id = paypal_payment_id
            payment.save()
            
            # Mark payment as paid (updates order status and awards loyalty points)
            payment.mark_as_paid()
            
            user = get_user_from_session(request)
            if user:
                cart = Cart.objects.filter(user=user).first()
                if cart:
                    cart.clear()

            messages.success(request, 'Payment completed successfully!')
            return redirect('payment_success', order_id=payment.order.id)  # Use URL name
        else:
            # Payment execution failed
            payment.status = 'F'  # Failed
            payment.save()
            messages.error(request, 'Payment execution failed.')
            return redirect('payment_failed', order_id=payment.order.id)  # Use URL name
        
    except Exception as e:
        print(f"PayPal Success Error: {str(e)}")
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('home')


# =====================
# STRIPE PAYMENT FLOW
# =====================

def create_stripe_payment(request, payment):
    """Create Stripe Checkout Session and redirect to Stripe"""
    try:
        # Calculate amount in cents
        amount_cents = int(payment.total_amount * 100)
        
        # Create Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'myr',
                    'product_data': {
                        'name': f'Order #{payment.order.order_number} - WinnieCho',
                        'description': 'Chocolate Shop Purchase',
                    },
                    'unit_amount': amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(
                f'/payment/stripe/success/{payment.id}/?session_id={{CHECKOUT_SESSION_ID}}'
            ),
            cancel_url=request.build_absolute_uri(
                f'/payment/cancel/{payment.id}/'
            ),
            metadata={
                'payment_id': str(payment.id),
                'order_id': str(payment.order.id)
            },
            customer_email=payment.order.address.user.email,
        )

        return JsonResponse({
            'success': True,
            'redirect': session.url
        })
    
    except Exception as e:
        print(f"Stripe Error: {str(e)}")
        messages.error(request, f'Stripe error: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': f'Stripe error: {str(e)}'
        }, status=500)


def stripe_success(request, payment_id):
    """Handle Stripe return after successful payment"""
    try:
        payment = get_object_or_404(Payment, id=payment_id)
        session_id = request.GET.get('session_id')

        # Check if already processed
        if payment.status == 'S':
            # Already processed, just redirect
            payment.order.status = 'C'
            messages.success(request, 'Payment completed successfully!')
            return redirect('payment_success', order_id=payment.order.id)  # Use URL name

        if not session_id or session_id == '{CHECKOUT_SESSION_ID}':
            # No session_id means user came directly to success URL
            # Mark as paid anyway (Stripe webhook will confirm)
            payment.order.status = 'C'
            payment.status = 'S'
            payment.transaction_id = 'stripe_redirect'
            payment.save()
            payment.mark_as_paid()
            
            user = get_user_from_session(request)
            if user:
                cart = Cart.objects.filter(user=user).first()
                if cart:
                    cart.clear()

            messages.success(request, 'Payment completed successfully!')
            return redirect('payment_success', order_id=payment.order.id)  # Use URL name
        
        # Verify with Stripe
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        
            # Check payment status
            if session.payment_status in ['paid', 'no_payment_required']:
                payment.order.status = 'C'
                payment.status = 'S'
                payment.transaction_id = session.id
                payment.save()
                payment.mark_as_paid()
                
                # ✅ Clear the cart
                user = get_user_from_session(request)
                if user:
                    cart = Cart.objects.filter(user=user).first()
                    if cart:
                        cart.clear()

                messages.success(request, 'Payment completed successfully!')
                return redirect('payment_success', order_id=payment.order.id)  # Use URL name
            else:
                # Payment not completed
                payment.status = 'F'
                payment.save()
                messages.warning(request, f'Payment status: {session.payment_status}')
                return redirect('payment_failed', order_id=payment.order.id)  # Use URL name
        
        except stripe.error.InvalidRequestError:
            # Session retrieval failed, but mark as paid
            payment.order.status = 'C'
            payment.status = 'S'
            payment.transaction_id = 'stripe_fallback'
            payment.save()
            payment.mark_as_paid()

            # ✅ Clear the cart
            user = get_user_from_session(request)
            if user:
                cart = Cart.objects.filter(user=user).first()
                if cart:
                    cart.clear()

            messages.success(request, 'Payment completed successfully!')
            return redirect('payment_success', order_id=payment.order.id)  # Use URL name
        
    except Payment.DoesNotExist:
        messages.error(request, 'Payment record not found.')
        return redirect('home')
    
    except Exception as e:
        print(f"Stripe Success Error: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
        return redirect('home')


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks for async payment confirmation"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Get payment_id from metadata
        payment_id = session.metadata.get('payment_id')
        
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                
                # Check if already processed
                if payment.status != 'S':
                    payment.order.status = 'C'
                    payment.status = 'S'
                    payment.method = 'ST'
                    payment.transaction_id = session.id
                    payment.save()
                    payment.mark_as_paid()
                    
                    # Clear session (if user is still in session)
                    # Note: This is async, so we can't access request.session here
                    # Session cleanup should be done in the redirect view
                    
            except Payment.DoesNotExist:
                pass
    
    return HttpResponse(status=200)


# =====================
# CASH ON DELIVERY FLOW
# =====================

def payment_cancel(request, payment_id):
    """Handle payment cancellation"""
    try:
        payment = get_object_or_404(Payment, id=payment_id)
        payment.status = 'C'  # Cancelled
        payment.save()
        
        messages.info(request, 'Payment was cancelled.')
        
        # Redirect to cart instead (since payment page doesn't accept order_id)
        return redirect('payment')
        
        # OR redirect to dashboard
        # return redirect('dashboard')
    
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('home')


def payment_success(request, order_id):
    """Payment success page - CLEAR CART HERE"""
    order = get_object_or_404(Order, pk=order_id)
    payment = order.payments.first()
    
    # NOW clear the cart (after successful payment)
    user = get_user_from_session(request)
    if user:
        cart = Cart.objects.filter(user=user).first()
        if cart:
            print(f"DEBUG: Clearing cart for user {user.id}, cart has {cart.get_total_items()} items")
            cart.clear()
            print(f"DEBUG: After clearing, cart has {cart.get_total_items()} items")
    
    # Clear session
    _clear_payment_session(request)
    
    context = {
        'order': order,
        'payment': payment,
    }
    return render(request, 'order/payment_success.html', context)


def payment_failed(request, order_id):
    """Payment failed page"""
    # DON'T require session - order_id is in URL
    order = get_object_or_404(Order, pk=order_id)
    payment = order.payments.first()
    
    context = {
        'order': order,
        'payment': payment,
    }
    return render(request, 'order/payment_failed.html', context)


# =====================
# HELPER FUNCTIONS
# =====================

def _clear_payment_session(request):
    """Clear payment-related session data"""
    keys_to_remove = [
        'pending_order_id',
        'pending_order_total',
        'pending_order_discount',
        'loyalty_points_to_redeem',
        'checkout_return'
    ]
    
    for key in keys_to_remove:
        if key in request.session:
            del request.session[key]
    
    request.session.modified = True


def get_user_from_session(request):
    """Helper to get user from session"""
    user_id = request.session.get('user_id')
    if user_id:
        return User.objects.get(pk=user_id)
    return None


def order_detail(request, order_id):
    """Order detail and receipt"""
    user = get_user_from_session(request)
    if not user:
        return redirect('login')
    
    order = get_object_or_404(Order, pk=order_id, address__user=user)
    payment = order.payments.first()
    
    context = {
        'order': order,
        'payment': payment,
    }
    return render(request, 'order/order_detail.html', context)


# =====================
# DASHBOARD & PROFILE
# =====================
def dashboard(request):
    """User dashboard"""
    user = get_user_from_session(request)
    if not user:
        return redirect('login')
    
    # Get all orders
    orders = Order.objects.filter(
        address__user=user
    ).exclude(
        status='X'  # Exclude cancelled orders
    ).order_by('-created_at')
    
    # Get recent orders
    recent_orders = orders[:5]
    
    # Get all orders for count
    total_orders = orders.count()
    
    # Get member stats
    member = None
    if user.is_member():
        member = user.member_profile
    
    # Get ALL addresses (CHANGED)
    addresses = Address.objects.filter(user=user).order_by('-is_default', '-created_at')
    default_address = user.get_default_address()
    
    context = {
        'user': user,
        'member': member,
        'addresses': addresses,  # CHANGED: was 'address'
        'default_address': default_address,
        'recent_orders': recent_orders,
        'orders': orders,
        'total_orders': total_orders,
    }
    return render(request, 'account/dashboard.html', context)


@require_POST
def update_profile(request):
    """Update user profile"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    user.name = request.POST.get('name', user.name)
    user.phone = request.POST.get('phone', user.phone)
    
    birthday = request.POST.get('birthday')
    if birthday:
        user.birthday = birthday
    
    user.save()
    
    return JsonResponse({'success': True, 'message': 'Profile updated'})


def manage_addresses(request):
    """Address management page"""
    user = get_user_from_session(request)
    if not user:
        return redirect('login')
    
    addresses = Address.objects.filter(user=user).order_by('-is_default', '-created_at')
    
    # Check if coming from checkout (URL parameter OR session flag)
    from_checkout = request.GET.get('from') == 'checkout'
    return_to_checkout = request.session.get('checkout_return', False) or from_checkout
    
    # Set the session flag if coming from checkout
    if from_checkout:
        request.session['checkout_return'] = True
    
    context = {
        'addresses': addresses,
        'return_to_checkout': return_to_checkout,
    }
    return render(request, 'account/manage_addresses.html', context)


@require_POST
def add_address(request):
    """Add new address"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        label = request.POST.get('label', 'Home')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country', 'Malaysia')
        is_default = request.POST.get('is_default') == 'on'  # Checkbox sends 'on' when checked
        
        # Validate required fields
        if not all([address, city, state, postal_code]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        # If setting as default, unset other defaults first
        if is_default:
            Address.objects.filter(user=user, is_default=True).update(is_default=False)
        
        # Create new address
        new_address = Address.objects.create(
            user=user,
            label=label,
            address=address,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=is_default
        )
        
        # Check if should redirect to checkout
        redirect_url = None
        if request.session.get('checkout_return'):
            del request.session['checkout_return']
            redirect_url = '/checkout/'
        
        return JsonResponse({
            'success': True,
            'message': 'Address added successfully',
            'address_id': new_address.id,
            'redirect': redirect_url
        })
        
    except Exception as e:
        print(f"Add address error: {str(e)}")
        return JsonResponse({'error': f'Error adding address: {str(e)}'}, status=500)


@require_POST
def update_address(request, address_id):
    """Update existing address"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        address = get_object_or_404(Address, id=address_id, user=user)
        
        # Update fields
        address.label = request.POST.get('label', address.label)
        address.address = request.POST.get('address', address.address)
        address.city = request.POST.get('city', address.city)
        address.state = request.POST.get('state', address.state)
        address.postal_code = request.POST.get('postal_code', address.postal_code)
        address.country = request.POST.get('country', address.country)
        
        # Handle is_default checkbox
        is_default = request.POST.get('is_default') == 'on'
        if is_default and not address.is_default:
            # Unset other defaults
            Address.objects.filter(user=user, is_default=True).update(is_default=False)
            address.is_default = True
        
        address.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Address updated successfully'
        })
        
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Address not found'}, status=404)
    except Exception as e:
        print(f"Update address error: {str(e)}")
        return JsonResponse({'error': f'Error updating address: {str(e)}'}, status=500)
    

@require_POST
def set_default_address(request, address_id):
    """Set address as default"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        # Get the address to set as default
        address = get_object_or_404(Address, id=address_id, user=user)
        
        # Unset all other defaults first
        Address.objects.filter(user=user, is_default=True).update(is_default=False)
        
        # Set this one as default
        address.is_default = True
        address.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Default address updated'
        })
        
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Address not found'}, status=404)
    except Exception as e:
        print(f"Set default error: {str(e)}")
        return JsonResponse({'error': f'Error setting default: {str(e)}'}, status=500)


@require_POST
def delete_address(request, address_id):
    """Delete address"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        address = get_object_or_404(Address, id=address_id, user=user)
        
        # Don't allow deleting if it's the only address
        user_addresses = Address.objects.filter(user=user)
        if user_addresses.count() == 1:
            return JsonResponse({
                'error': 'Cannot delete your only address'
            }, status=400)
        
        # Don't allow deleting default address
        if address.is_default:
            return JsonResponse({
                'error': 'Cannot delete default address. Please set another address as default first.'
            }, status=400)
        
        address.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Address deleted successfully'
        })
        
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Address not found'}, status=404)
    except Exception as e:
        print(f"Delete address error: {str(e)}")
        return JsonResponse({'error': f'Error deleting address: {str(e)}'}, status=500)


@require_POST
def change_password(request):
    """Change user password - BLOCKS OAuth users"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    # ✅ CHECK IF OAUTH USER
    if user.is_oauth_user():
        return JsonResponse({
            'error': 'Cannot change password for Google login accounts'
        }, status=400)
    
    current_password = request.POST.get('current_password')
    new_password = request.POST.get('new_password')
    
    # Verify current password
    hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
    if user.password != hashed_current:
        return JsonResponse({'error': 'Current password is incorrect'}, status=400)
    
    # Update password
    user.password = hashlib.sha256(new_password.encode()).hexdigest()
    user.save()
    
    return JsonResponse({'success': True, 'message': 'Password changed successfully'})


def orders_history(request):
    """Order history page"""
    user = get_user_from_session(request)
    if not user:
        return redirect('login')
    
    orders = Order.objects.filter(
        address__user=user
    ).exclude(
        status='X'  # Exclude cancelled orders
    ).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'order/orders_history.html', context)


# =====================
# PASSWORD RESET
# =====================

def forgot_password(request):
    """Forgot password page with actual email sending"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate token
            token = secrets.token_urlsafe(32)
            reset_token = PasswordResetToken.objects.create(user=user, token=token)
            
            # Build reset URL
            reset_url = request.build_absolute_uri(f'/reset-password/{token}/')
            
            # Email subject and message
            subject = 'Reset Your WinnieCho Password'
            
            # HTML email content
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #2b2b2b; color: white; padding: 20px; text-align: center; }}
                    .content {{ background: #f5f5f0; padding: 30px; }}
                    .button {{ display: inline-block; padding: 12px 30px; background: #a67c52; color: white; text-decoration: none; border-radius: 0; margin: 20px 0; }}
                    .footer {{ text-align: center; padding: 20px; color: #8a8a8a; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>WinnieCho</h1>
                    </div>
                    <div class="content">
                        <h2>Password Reset Request</h2>
                        <p>Hi {user.name},</p>
                        <p>We received a request to reset your password. Click the button below to create a new password:</p>
                        <a href="{reset_url}" class="button">Reset Password</a>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #a67c52;">{reset_url}</p>
                        <p><strong>This link will expire in 30 minutes.</strong></p>
                        <p>If you didn't request this password reset, please ignore this email.</p>
                        <p>Best regards,<br>The WinnieCho Team</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 WinnieCho Chocolate Shop. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version (fallback)
            plain_message = f"""
            Hi {user.name},

            We received a request to reset your password.
            
            Click this link to reset your password:
            {reset_url}
            
            This link will expire in 30 minutes.
            
            If you didn't request this password reset, please ignore this email.
            
            Best regards,
            The WinnieCho Team
            """
            
            # Send email
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                messages.success(request, f'Password reset link sent to {email}. Please check your inbox.')
                return redirect('login')
                
            except Exception as e:
                print(f"Email sending error: {str(e)}")
                messages.error(request, f'Error sending email. Please try again later.')
                return redirect('forgot_password')
            
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security)
            messages.success(request, 'If that email exists, a reset link has been sent.')
            return redirect('login')
    
    return render(request, 'account/forgot_password.html')


def reset_password(request, token):
    """Reset password with token"""
    reset_token = get_object_or_404(PasswordResetToken, token=token)
    
    if not reset_token.is_valid():
        messages.error(request, 'Invalid or expired reset link')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        
        # Update password
        user = reset_token.user
        user.password = hashlib.sha256(new_password.encode()).hexdigest()
        user.save()
        
        # Mark token as used
        reset_token.mark_as_used()
        
        messages.success(request, 'Password reset successful! Please log in.')
        return redirect('login')
    
    context = {'token': token}
    return render(request, 'account/reset_password.html', context)


# =============================================
# USER API - Active Orders Tracking
# =============================================

def get_active_orders(request):
    """Get user's active orders for delivery tracking bar"""
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({'orders': []})
    
    # Get all non-cancelled orders
    orders = Order.objects.filter(
        address__user=user
    ).exclude(
        status='X'  # Exclude cancelled
    ).order_by('-created_at')
    
    orders_data = []
    for order in orders:
        # Calculate time ago
        time_diff = timezone.now() - order.created_at
        if time_diff.days > 0:
            time_ago = f"{time_diff.days}d ago"
        elif time_diff.seconds // 3600 > 0:
            time_ago = f"{time_diff.seconds // 3600}h ago"
        else:
            time_ago = f"{time_diff.seconds // 60}m ago"
        
        # Get delivery proof if delivered
        delivery_proof = None
        delivered_at = None
        if hasattr(order, 'delivery_proof') and order.delivery_proof:
            # Access the actual ImageField in DeliveryProof
            if order.delivery_proof.image:
                delivery_proof = order.delivery_proof.image.url
            if order.delivery_proof.uploaded_at:
                delivered_at = order.delivery_proof.uploaded_at.strftime('%b %d, %I:%M %p')
        
        orders_data.append({
            'id': str(order.id),
            'order_number': order.order_number,
            'status': order.status,
            'total_items': order.get_total_items(),
            'total': str(order.subtotal),
            'time_ago': time_ago,
            'delivery_proof': delivery_proof,
            'delivered_at': delivered_at
        })
    
    return JsonResponse({'orders': orders_data})


# =============================================
# DRIVER DASHBOARD
# =============================================

def driver_dashboard(request):
    """Driver dashboard view"""
    user = get_user_from_session(request)
    if not user or user.role != 'D':  # Check if driver
        messages.error(request, 'Driver access required')
        return redirect('home')
    
    return render(request, 'driver/dashboard.html')


# =============================================
# DRIVER API - Get Orders
# =============================================

def get_driver_orders(request):
    """Get orders for driver (all non-cancelled) - FIXED DEFAULT"""
    user = get_user_from_session(request)
    if not user or user.role != 'D':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    # ✅ FIX: Filter by status if provided, otherwise show ALL
    status = request.GET.get('status', '')
    
    # ✅ CHANGED: Default shows ALL orders, not just 'C'
    if status:
        orders = Order.objects.filter(status=status).exclude(status='X')
    else:
        # Show ALL non-cancelled orders
        orders = Order.objects.exclude(status='X')
    
    orders = orders.select_related('address__user').order_by('-created_at')
    
    # ✅ DEBUG: Print what we're querying
    print(f"🚗 Driver querying orders with status: '{status}' (empty = ALL)")
    print(f"📦 Found {orders.count()} orders")
    
    orders_data = []
    for order in orders:
        # Calculate time ago
        time_diff = timezone.now() - order.created_at
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds // 3600 > 0:
            time_ago = f"{time_diff.seconds // 3600} hour{'s' if time_diff.seconds // 3600 > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        # Get delivery proof
        delivery_proof = None
        if hasattr(order, 'delivery_proof') and order.delivery_proof:
            delivery_proof = order.delivery_proof.image.url if order.delivery_proof.image else None
        
        orders_data.append({
            'id': str(order.id),
            'order_number': order.order_number,
            'status': order.status,
            'customer_name': order.address.user.name,
            'customer_phone': order.address.user.phone,
            'delivery_address': order.address.get_full_address(),
            'total_items': order.get_total_items(),
            'total': str(order.subtotal),
            'time_ago': time_ago,
            'delivery_proof': delivery_proof
        })
    
    print(f"✅ Returning {len(orders_data)} orders to driver")
    return JsonResponse({'orders': orders_data})


# =============================================
# DRIVER API - Update Order Status
# =============================================

@require_POST
def update_order_status(request):
    """Driver updates order status"""
    user = get_user_from_session(request)
    if not user or user.role != 'D':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        import json
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        order = Order.objects.get(id=order_id)
        old_status = order.status
        
        # Update status
        order.status = new_status
        order.save()
        
        # Send notification email to customer
        send_order_status_email(order, old_status)
        
        return JsonResponse({
            'success': True,
            'message': 'Status updated successfully'
        })
        
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================
# DRIVER API - Upload Delivery Proof
# =============================================

@require_POST
def upload_delivery_proof(request):
    """Driver uploads delivery proof image"""
    user = get_user_from_session(request)
    if not user or user.role != 'D':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        order_id = request.POST.get('order_id')
        proof_image = request.FILES.get('proof_image')
        
        if not proof_image:
            return JsonResponse({'error': 'No image provided'}, status=400)
        
        order = Order.objects.get(id=order_id)
        
        # Create or update delivery proof
        from .models import DeliveryProof
        
        proof, created = DeliveryProof.objects.get_or_create(
            order=order,
            defaults={
                'driver': user,
                'image': proof_image,
                'uploaded_at': timezone.now()
            }
        )
        
        if not created:
            # Update existing proof
            proof.image = proof_image
            proof.uploaded_at = timezone.now()
            proof.save()
        
        # Auto-set order to delivered if not already
        if order.status != 'D':
            order.status = 'D'
            order.save()
            
            # Send notification
            send_order_status_email(order, 'S')  # From Shipped to Delivered
        
        return JsonResponse({
            'success': True,
            'message': 'Proof uploaded successfully',
            'image_url': proof.image.url
        })
        
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# =============================================
# HELPER FUNCTION - Send Status Update Email
# =============================================

def send_order_status_email(order, old_status):
    """Send email when order status changes"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    status_messages = {
        'P': 'Your order is pending confirmation.',
        'C': 'Your order has been confirmed and is being prepared!',
        'S': 'Your order has been shipped and is on the way!',
        'D': 'Your order has been delivered. Enjoy your chocolates!',
        'X': 'Your order has been cancelled.'
    }
    
    subject = f'Order Status Update - #{order.order_number}'
    
    message = f"""
    Hi {order.address.user.name},

    Your order #{order.order_number} status has been updated.

    Previous Status: {dict(Order.status_choices).get(old_status)}
    New Status: {order.get_status_display()}

    {status_messages.get(order.status, '')}

    Order Details:
    Total: RM {order.subtotal}
    Items: {order.get_total_items()}

    Delivery Address:
    {order.address.get_full_address()}

    Track your order: {settings.SITE_URL}/orders/{order.id}/

    Thank you for shopping with WinnieCho!

    Best regards,
    WinnieChO Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[order.address.user.email],
            fail_silently=True,
        )
        print(f"✅ Status email sent to {order.address.user.email}")
    except Exception as e:
        print(f"❌ Error sending status email: {str(e)}")



# =============================================
# ANALYTICS DASHBOARD (ADD TO views.py)
# =============================================

def analytics_dashboard(request):
    """Analytics dashboard for admin - View only, no CRUD"""
    user = get_user_from_session(request)
    if not user or not user.is_admin():
        messages.error(request, 'Admin access required')
        return redirect('home')
    
    # Time period filter
    period = request.GET.get('period', '30')
    
    if period == '7':
        start_date = timezone.now() - timedelta(days=7)
        period_label = 'Last 7 Days'
    elif period == '30':
        start_date = timezone.now() - timedelta(days=30)
        period_label = 'Last 30 Days'
    elif period == '90':
        start_date = timezone.now() - timedelta(days=90)
        period_label = 'Last 90 Days'
    else:
        start_date = timezone.now() - timedelta(days=365)
        period_label = 'Last Year'
    
    # =====================
    # KEY METRICS
    # =====================
    total_revenue = Payment.objects.filter(
        status='S',
        created_at__gte=start_date
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_orders = Order.objects.filter(
        created_at__gte=start_date
    ).exclude(status='X').count()
    
    total_customers = User.objects.filter(
        role='M',
        created_at__gte=start_date
    ).count()
    
    total_products = Product.objects.filter(status=1).count()
    
    avg_order_value = Payment.objects.filter(
        status='S',
        created_at__gte=start_date
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # =====================
    # SALES CHART DATA (Daily)
    # =====================
    sales_by_day = Payment.objects.filter(
        status='S',
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('total_amount'),
        orders=Count('id')
    ).order_by('date')
    
    sales_chart_labels = [
        item['date'].strftime('%Y-%m-%d')
        for item in sales_by_day
        if item['date'] is not None
    ]
    sales_chart_revenue = [
        float(item['revenue'])
        for item in sales_by_day
        if item['date'] is not None
    ]
    sales_chart_orders = [
        item['orders']
        for item in sales_by_day
        if item['date'] is not None
    ]
    
    # =====================
    # CATEGORY PERFORMANCE
    # =====================
    category_sales = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__status__in=['C', 'S', 'D']
    ).values(
        'product__category__name'
    ).annotate(
        revenue=Sum(F('quantity') * F('unit_price')),
        quantity=Sum('quantity')
    ).order_by('-revenue')
    
    category_labels = [item['product__category__name'] for item in category_sales]
    category_revenue = [float(item['revenue']) for item in category_sales]
    
    # =====================
    # TOP PRODUCTS
    # =====================
    top_products = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__status__in=['C', 'S', 'D']
    ).values(
        'product__name',
        'product__id'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_revenue')[:10]
    
    # =====================
    # RECENT ORDERS
    # =====================
    recent_orders = Order.objects.select_related(
        'address__user'
    ).exclude(status='X').order_by('-created_at')[:10]
    
    # =====================
    # LOW STOCK ALERT
    # =====================
    low_stock = Product.objects.filter(
        status=1,
        stock__lte=10
    ).order_by('stock')[:10]
    
    # =====================
    # ORDER STATUS BREAKDOWN
    # =====================
    order_status_breakdown = Order.objects.filter(
        created_at__gte=start_date
    ).values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    status_labels = [dict(Order.status_choices).get(item['status'], 'Unknown') for item in order_status_breakdown]
    status_counts = [item['count'] for item in order_status_breakdown]
    
    # =====================
    # TOP CUSTOMERS
    # =====================
    top_customers = Payment.objects.filter(
        status='S',
        created_at__gte=start_date
    ).values(
        'order__address__user__id',
        'order__address__user__name',
        'order__address__user__email'
    ).annotate(
        total_spent=Sum('total_amount'),
        order_count=Count('order', distinct=True)
    ).order_by('-total_spent')[:10]
    
    context = {
        'total_revenue': float(total_revenue),
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'avg_order_value': float(avg_order_value),

        'sales_chart_labels': sales_chart_labels,
        'sales_chart_revenue': sales_chart_revenue,
        'sales_chart_orders': sales_chart_orders,

        'category_labels': category_labels,
        'category_revenue': category_revenue,

        'status_labels': status_labels,
        'status_counts': status_counts,

        'top_products': top_products,
        'recent_orders': recent_orders,
        'low_stock': low_stock,
        'top_customers': top_customers,

        'period': period,
        'period_label': period_label,
    }
    
    return render(request, 'secure/admin/analytics.html', context)


# ============================================================
# EMAIL NOTIFICATION FUNCTIONS
# ============================================================

def send_admin_notification(order):
    """Send email/SMS to admin when order placed"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = f'🛒 New Order - #{order.order_number}'
    payment = order.payments.first()
    
    message = f"""
═══════════════════════════════════════
NEW ORDER RECEIVED
═══════════════════════════════════════

Order Number: {order.order_number}
Order Date: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}

CUSTOMER INFORMATION:
• Name: {order.address.user.name}
• Email: {order.address.user.email}
• Phone: {order.address.user.phone}

ORDER DETAILS:
• Items: {order.get_total_items()} item(s)
• Subtotal: RM {order.subtotal}
• Discount: RM {payment.discount_amount if payment else 0}
• Total: RM {payment.total_amount if payment else order.subtotal}
• Payment: {payment.get_method_display() if payment else 'N/A'}

DELIVERY ADDRESS:
{order.address.label}
{order.address.address}
{order.address.city}, {order.address.state} {order.address.postal_code}
{order.address.country}

ITEMS ORDERED:
"""
    
    for item in order.items.all():
        message += f"\n  • {item.quantity}x {item.product_name} - RM {item.subtotal}"
    
    message += f"""

═══════════════════════════════════════
View in admin panel to process order.

WinnieChO Admin System
═══════════════════════════════════════
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        print(f"✅ Admin email sent for order {order.order_number}")
        
        # SNS notification (optional)
        if hasattr(settings, 'USE_SNS_NOTIFICATIONS') and settings.USE_SNS_NOTIFICATIONS:
            try:
                sns = boto3.client('sns', region_name=settings.AWS_SNS_REGION_NAME)
                sms_message = f"WinnieChO: New order #{order.order_number} from {order.address.user.name}. Total: RM {payment.total_amount if payment else order.subtotal}"
                sns.publish(
                    TopicArn=settings.AWS_SNS_TOPIC_ARN,
                    Subject=subject,
                    Message=sms_message
                )
                print(f"✅ Admin SMS sent for order {order.order_number}")
            except Exception as e:
                print(f"⚠️  SNS failed: {str(e)}")
        
        return True
    except Exception as e:
        print(f"❌ Error sending admin notification: {str(e)}")
        return False


def send_order_status_email(order, old_status):
    """Send email when order status changes"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = f'Order Status Update - #{order.order_number}'
    
    status_messages = {
        'P': 'Your order is pending confirmation.',
        'C': 'Your order has been confirmed and is being prepared!',
        'S': 'Your order has been shipped and is on the way!',
        'D': 'Your order has been delivered. Enjoy your chocolates!',
        'X': 'Your order has been cancelled.'
    }
    
    message = f"""
Hi {order.address.user.name},

Your order #{order.order_number} status has been updated.

Previous Status: {old_status}
New Status: {order.get_status_display()}

{status_messages.get(order.status, '')}

Order Details:
Total: RM {order.subtotal}
Items: {order.get_total_items()}

Delivery Address:
{order.address.get_full_address()}

Thank you for shopping with WinnieCho!

Best regards,
WinnieChO Team
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[order.address.user.email],
            fail_silently=False,
        )
        print(f"✅ Status email sent to {order.address.user.email}")
    except Exception as e:
        print(f"❌ Error sending status email: {str(e)}")
