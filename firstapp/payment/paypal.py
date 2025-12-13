import paypalrestsdk
from django.conf import settings

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # sandbox or live
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET
})

def create_payment(amount, return_url, cancel_url, description="Chocolate Order"):
    """Create PayPal payment"""
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url
        },
        "transactions": [{
            "amount": {
                "total": str(amount),
                "currency": "MYR"
            },
            "description": description
        }]
    })

    if payment.create():
        # Get approval URL
        for link in payment.links:
            if link.rel == "approval_url":
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'approval_url': link.href
                }
    else:
        return {
            'success': False,
            'error': payment.error
        }

def execute_payment(payment_id, payer_id):
    """Execute approved PayPal payment"""
    payment = paypalrestsdk.Payment.find(payment_id)
    
    if payment.execute({"payer_id": payer_id}):
        return {
            'success': True,
            'payment_id': payment.id,
            'state': payment.state,
            'transactions': payment.transactions
        }
    else:
        return {
            'success': False,
            'error': payment.error
        }

def get_payment_details(payment_id):
    """Get payment details"""
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        return {
            'success': True,
            'payment': payment
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }