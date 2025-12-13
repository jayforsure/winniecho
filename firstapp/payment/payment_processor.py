from .stripe_payment import create_payment_intent, create_checkout_session
from .paypal import create_payment as create_paypal_payment, execute_payment

class PaymentProcessor:
    """Unified payment processor for all payment methods"""
    
    @staticmethod
    def process_stripe_payment(amount, metadata=None):
        """Process Stripe payment"""
        return create_payment_intent(amount, metadata=metadata)
    
    @staticmethod
    def process_paypal_payment(amount, return_url, cancel_url):
        """Process PayPal payment"""
        return create_paypal_payment(amount, return_url, cancel_url)
    
    @staticmethod
    def process_cod_payment(order_id):
        """Process Cash on Delivery"""
        return {
            'success': True,
            'payment_method': 'COD',
            'order_id': order_id,
            'message': 'Order placed. Pay on delivery.'
        }
    
    @staticmethod
    def complete_paypal_payment(payment_id, payer_id):
        """Complete PayPal payment after approval"""
        return execute_payment(payment_id, payer_id)