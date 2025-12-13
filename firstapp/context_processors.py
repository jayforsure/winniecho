from .models import User, Member, Cart

def user_context(request):
    """
    Add user info and cart count to all templates
    """
    context = {
        'is_logged_in': False,
        'is_admin': False,
        'current_user': None,
        'cart_count': 0,
    }
    
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            context['is_logged_in'] = True
            context['current_user'] = user
            
            # Check if admin
            if user.role == 'A':
                try:
                    context['is_admin'] = True
                except Member.DoesNotExist:
                    pass
            
            # Get cart count
            try:
                cart = Cart.objects.get(user=user)
                context['cart_count'] = cart.get_total_items()
            except Cart.DoesNotExist:
                pass
                
        except User.DoesNotExist:
            pass
    
    return context