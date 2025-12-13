# firstapp/pipeline.py
# FIXED: Correct pipeline for Google OAuth integration

from django.contrib.auth.models import User as AuthUser
from .models import User, Member, Cart

def create_user_profile(backend, user, response, *args, **kwargs):
    """
    Custom pipeline to create User, Member, and Cart after Google OAuth.
    
    IMPORTANT: This runs AFTER social-auth creates the Django auth.User
    So 'user' parameter is already a Django User (auth.User)
    We need to create our custom User model based on it
    """
    if backend.name == 'google-oauth2':
        # Get user info from Google
        email = response.get('email')
        name = response.get('name', email.split('@')[0])
        
        request = kwargs.get('request')
        
        try:
            # Try to get existing custom user by email
            custom_user = User.objects.get(email=email)
            print(f"✅ Google OAuth: Existing user found - {email}")
            
        except User.DoesNotExist:
            # Create new custom user
            custom_user = User.objects.create(
                email=email,
                name=name,
                password='',  # No password for OAuth users
                role='M',     # Member role
                phone='',     # Will be updated later in profile
            )
            
            # Create Member profile
            Member.objects.create(user=custom_user)
            
            # Create Cart
            Cart.objects.create(user=custom_user)
            
            print(f"✅ Google OAuth: New user created - {email}")
        
        # Set session with custom user
        if request:
            request.session['user_id'] = custom_user.id
            request.session['user_name'] = custom_user.name
            request.session['user_email'] = custom_user.email
            print(f"✅ Session set: user_id={custom_user.id}")
    
    # IMPORTANT: Don't return anything or return empty dict
    # Let social-auth handle the auth.User
    return {}