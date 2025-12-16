"""
Django settings for chocolate_ordering_system project.
PRODUCTION CONFIGURATION FOR AWS DEPLOYMENT
"""
import pymysql
pymysql.install_as_MySQLdb()

import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'your-fallback-secret-key')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    '10.0.2.120',
    '10.0.1.248',
    '127.0.0.1',
    '54.209.180.169',
    'localhost',
    '.elb.amazonaws.com',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',  # If using OAuth
    'firstapp',  # Your app name
    'storages',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'firstproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'firstproject.wsgi.application'

# KMS Configuration
KMS_KEY_ID = os.getenv('KMS_KEY_ID')

# Use encrypted database password
ENCRYPTED_DB_PASSWORD = os.getenv('ENCRYPTED_DB_PASSWORD')

if ENCRYPTED_DB_PASSWORD:
    from firstapp.encryption import decrypt_secret
    DB_PASSWORD = decrypt_secret(ENCRYPTED_DB_PASSWORD)
else:
    DB_PASSWORD = os.getenv('DB_PASSWORD')

USE_RDS = os.getenv('USE_RDS', 'False') == 'True'
if not USE_RDS:
    # LOCAL DEVELOPMENT
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAMEl'),
            'USER': os.getenv('DB_USERl'),
            'PASSWORD': os.getenv('DB_PASSWORDl'),
            'HOST': os.getenv('DB_HOSTl'),
            'PORT': os.getenv('DB_PORTl'),
            'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
            },
            'PASSWORD': DB_PASSWORD,
        }
    }
else:
    # AWS RDS (PRODUCTION)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
            'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
            },
            'PASSWORD': DB_PASSWORD,
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kuala_Lumpur'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# S3 Configuration - NO KEYS NEEDED!
USE_S3 = os.getenv('USE_S3', 'False') == 'True'

if USE_S3:
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = 'us-east-1'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False  # No credentials needed!
    
    
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# SNS email
AWS_SNS_REGION_NAME = 'us-east-1'
AWS_SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:049585066686:winniecho-alerts'

# Email settings (if using)
if not DEBUG:
    EMAIL_BACKEND = 'firstapp.email_backends.SNSEmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS')
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Set True if using HTTPS
    SESSION_COOKIE_SECURE = False  # Set True if using HTTPS
    CSRF_COOKIE_SECURE = False  # Set True if using HTTPS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Proxy
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =====================
# AUTHENTICATION BACKENDS
# =====================

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

# =====================
# SOCIAL AUTH (GOOGLE OAUTH)
# =====================

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv(
    'GOOGLE_OAUTH2_KEY',
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv(
    'GOOGLE_OAUTH2_SECRET',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ['first_name', 'last_name']

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard/'
SOCIAL_AUTH_LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/dashboard/'

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'firstapp.pipeline.create_user_profile',
)

# =====================
# PAYMENT GATEWAYS
# =====================

# PayPal
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')
PAYPAL_CLIENT_ID = os.getenv(
    'PAYPAL_CLIENT_ID'
)
PAYPAL_CLIENT_SECRET = os.getenv(
    'PAYPAL_CLIENT_SECRET'
)

# Stripe
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Configure Gemini AI
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    except Exception as e:
        print(f"Gemini AI configuration error: {e}")
        GEMINI_AVAILABLE = False
else:
    GEMINI_AVAILABLE = False

# =====================
# LOGGING
# =====================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django_errors.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# =====================
# DEFAULT AUTO FIELD
# =====================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'