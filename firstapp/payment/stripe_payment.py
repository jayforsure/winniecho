import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_payment_intent(amount, currency='myr', metadata=None):
    """
    Create a Stripe Payment Intent
    amount: in cents (e.g., 5000 for RM 50.00)
    """
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            metadata=metadata or {},
            automatic_payment_methods={'enabled': True},
        )
        return {
            'success': True,
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id
        }
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'error': str(e)
        }

def confirm_payment(payment_intent_id):
    """Confirm a payment intent"""
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return {
            'success': True,
            'status': intent.status,
            'amount': intent.amount / 100
        }
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'error': str(e)
        }

def create_checkout_session(line_items, success_url, cancel_url, metadata=None):
    """Create a Stripe Checkout Session"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {},
        )
        return {
            'success': True,
            'session_id': session.id,
            'url': session.url
        }
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'error': str(e)
        }