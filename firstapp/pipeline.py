# firstapp/pipeline.py
# FIXED: Correct pipeline for Google OAuth integration

from django.contrib.auth.models import User as AuthUser
from .models import User, Member, Cart
from django.contrib import messages

def create_user_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'google-oauth2':
        email = response.get('email')
        name = response.get('name', email.split('@')[0])
        request = kwargs.get('request')
        
        try:
            custom_user = User.objects.get(email=email)
        except User.DoesNotExist:
            custom_user = User.objects.create(
                email=email,
                name=name,
                password='',
                role='M',
                phone='',
            )
            Member.objects.create(user=custom_user)
            Cart.objects.create(user=custom_user)
        
        if request:
            request.session['user_id'] = custom_user.id
            request.session['user_name'] = custom_user.name
            request.session['user_email'] = custom_user.email
            request.session['user_role'] = custom_user.role
            
            # ✅ ADD THIS: Django success message
            messages.success(request, f'Welcome back, {custom_user.name}!')
    
    return {}