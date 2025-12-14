from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.http import HttpResponse

urlpatterns = [
    path("health/", views.health, name='health'),
    
    # Public pages
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<str:token>/', views.reset_password, name='reset_password'),
    
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),  # ADD THIS
    
    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/process/', views.process_checkout, name='process_checkout'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/history/', views.orders_history, name='orders_history'),
    
    # Payment
    path('payment/', views.payment, name='payment'),
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/paypal/success/<int:payment_id>/', views.paypal_success, name='paypal_success'),
    path('payment/stripe/success/<int:payment_id>/', views.stripe_success, name='stripe_success'),
    path('payment/cancel/<int:payment_id>/', views.payment_cancel, name='payment_cancel'),
    path('payment/success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('payment/failed/<int:order_id>/', views.payment_failed, name='payment_failed'),
    path('payment/stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Dashboard & Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('password/change/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # Address Management - FIXED URLS
    path('manage_addresses/', views.manage_addresses, name='manage_addresses'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/<int:address_id>/update/', views.update_address, name='update_address'),
    path('addresses/<int:address_id>/set-default/', views.set_default_address, name='set_default_address'),
    path('addresses/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    
    # AI Chat
    path('ai_chat/', views.ai_chat_view, name='ai_chat'),
    
    # Admin
    path('admin_panel/', views.admin_dashboard, name='admin_dashboard'),

    path('auth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

