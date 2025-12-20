# """
# Django settings for WinnieChO project.
# PRODUCTION CONFIGURATION WITH EFS FOR SHARED MEDIA
# """
# import os
# from pathlib import Path
# import google.generativeai as genai
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# BASE_DIR = Path(__file__).resolve().parent.parent
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# # Security
# SECRET_KEY = os.getenv('SECRET_KEY', 'your-fallback-secret-key')
# DEBUG = os.getenv('DEBUG', 'False') == 'True'

# # ALLOWED_HOSTS for ALB
# ALLOWED_HOSTS = ['*']

# # Use X-Forwarded-Host header from ALB
# USE_X_FORWARDED_HOST = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# # Application definition
# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'social_django',
#     'firstapp',
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'whitenoise.middleware.WhiteNoiseMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'firstproject.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / 'templates'],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'firstproject.wsgi.application'

# # ============================================================
# # DATABASE CONFIGURATION
# # ============================================================

# USE_RDS = os.getenv('USE_RDS', 'False') == 'True'

# if not USE_RDS:
#     # LOCAL DEVELOPMENT
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.mysql',
#             'NAME': os.getenv('DB_NAMEl', 'winniecho'),
#             'USER': os.getenv('DB_USERl', 'root'),
#             'PASSWORD': os.getenv('DB_PASSWORDl', ''),
#             'HOST': os.getenv('DB_HOSTl', 'localhost'),
#             'PORT': os.getenv('DB_PORTl', '3306'),
#             'OPTIONS': {
#                 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#                 'charset': 'utf8mb4',
#             },
#         }
#     }
# else:
#     # AWS RDS (PRODUCTION)
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.mysql',
#             'NAME': os.getenv('DB_NAME', 'winniecho'),
#             'USER': os.getenv('DB_USER', 'admin'),
#             'PASSWORD': os.getenv('DB_PASSWORD'),
#             'HOST': os.getenv('DB_HOST'),
#             'PORT': os.getenv('DB_PORT', '3306'),
#             'OPTIONS': {
#                 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#                 'charset': 'utf8mb4',
#                 'connect_timeout': 10,
#             },
#             'CONN_MAX_AGE': 60,
#         }
#     }

# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
# ]

# # Internationalization
# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'Asia/Kuala_Lumpur'
# USE_I18N = True
# USE_TZ = True

# # ============================================================
# # EFS CONFIGURATION FOR SHARED MEDIA/STATIC FILES
# # ============================================================

# # ✅ EFS mount point (symlinks created by user-data script)
# EFS_AVAILABLE = os.path.islink('/opt/winniecho/media') or os.path.ismount('/mnt/efs')

# if EFS_AVAILABLE:
#     # ✅ Use symlinked directories (points to EFS)
#     MEDIA_ROOT = str(BASE_DIR / 'media')  # Symlink to /mnt/efs/media
#     STATIC_ROOT = str(BASE_DIR / 'staticfiles')  # Symlink to /mnt/efs/staticfiles
#     print(f"✓ Using EFS storage via symlinks")
#     print(f"  MEDIA_ROOT: {MEDIA_ROOT} -> {os.readlink(MEDIA_ROOT) if os.path.islink(MEDIA_ROOT) else 'not a link'}")
# else:
#     # Fallback to local storage
#     MEDIA_ROOT = str(BASE_DIR / 'media')
#     STATIC_ROOT = str(BASE_DIR / 'staticfiles')
#     print("⚠ Using local storage (EFS not detected)")

# # Media and static URLs
# MEDIA_URL = '/media/'
# STATIC_URL = '/static/'

# # Static files directories
# STATICFILES_DIRS = [
#     BASE_DIR / 'static',
# ]

# # Whitenoise for efficient static file serving
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# # ============================================================
# # FILE UPLOAD SETTINGS (OPTIMIZED FOR EFS)
# # ============================================================

# # Increased file upload limits
# FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
# DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# # Use temporary file uploads (better for EFS)
# FILE_UPLOAD_HANDLERS = [
#     'django.core.files.uploadhandler.TemporaryFileUploadHandler',
# ]

# # Temporary file upload directory
# FILE_UPLOAD_TEMP_DIR = '/tmp'

# # ============================================================
# # AUTHENTICATION
# # ============================================================

# AUTHENTICATION_BACKENDS = [
#     'social_core.backends.google.GoogleOAuth2',
#     'django.contrib.auth.backends.ModelBackend',
# ]

# # Google OAuth
# SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_OAUTH2_KEY')
# SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_OAUTH2_SECRET')
# SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
#     'https://www.googleapis.com/auth/userinfo.email',
#     'https://www.googleapis.com/auth/userinfo.profile',
# ]
# SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ['first_name', 'last_name']
# SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard/'
# SOCIAL_AUTH_LOGOUT_REDIRECT_URL = '/'
# LOGIN_URL = '/login/'
# LOGOUT_URL = '/logout/'
# LOGIN_REDIRECT_URL = '/dashboard/'

# SOCIAL_AUTH_PIPELINE = (
#     'social_core.pipeline.social_auth.social_details',
#     'social_core.pipeline.social_auth.social_uid',
#     'social_core.pipeline.social_auth.auth_allowed',
#     'social_core.pipeline.social_auth.social_user',
#     'social_core.pipeline.user.get_username',
#     'social_core.pipeline.user.create_user',
#     'firstapp.pipeline.create_user_profile',
#     'social_core.pipeline.social_auth.associate_user',
#     'social_core.pipeline.social_auth.load_extra_data',
#     'social_core.pipeline.user.user_details',
# )

# # ============================================================
# # PAYMENT GATEWAYS
# # ============================================================

# PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')
# PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
# PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')

# STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
# STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
# STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# # ============================================================
# # EMAIL & NOTIFICATIONS
# # ============================================================

# ADMIN_EMAIL = 'winniechoofficial@gmail.com'
# USE_SNS_NOTIFICATIONS = False  # ✅ Changed to False to use SMTP

# SITE_URL = os.getenv('SITE_URL', 'http://winniecho-alb-1199297198.us-east-1.elb.amazonaws.com')

# AWS_SNS_REGION_NAME = AWS_REGION
# AWS_SNS_TOPIC_ARN = os.getenv('AWS_SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:049585066686:winniecho-alerts')

# # ✅ ALWAYS USE SMTP (simpler than SNS)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
# EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
# EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# # ============================================================
# # GEMINI AI
# # ============================================================

# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
# if GEMINI_API_KEY:
#     try:
#         genai.configure(api_key=GEMINI_API_KEY)
#         GEMINI_AVAILABLE = True
#     except Exception as e:
#         print(f"Gemini AI configuration error: {e}")
#         GEMINI_AVAILABLE = False
# else:
#     GEMINI_AVAILABLE = False

# # ============================================================
# # SECURITY SETTINGS
# # ============================================================

# if not DEBUG:
#     # Don't force HTTPS (ALB handles it)
#     SECURE_SSL_REDIRECT = False
#     SESSION_COOKIE_SECURE = False
#     CSRF_COOKIE_SECURE = False
    
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     X_FRAME_OPTIONS = 'SAMEORIGIN'
    
#     # Don't use HSTS (ALB handles it)
#     SECURE_HSTS_SECONDS = 0
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = False
#     SECURE_HSTS_PRELOAD = False

# # CSRF Trusted Origins for ALB
# CSRF_TRUSTED_ORIGINS = [
#     'http://winniecho-alb-1199297198.us-east-1.elb.amazonaws.com',
#     'https://winniecho-alb-1199297198.us-east-1.elb.amazonaws.com',
# ]

# # ============================================================
# # LOGGING
# # ============================================================

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '[{levelname}] {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'INFO',
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#         },
#         'file': {
#             'level': 'WARNING',
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': '/var/log/django/django.log',
#             'maxBytes': 1024 * 1024 * 10,
#             'backupCount': 5,
#             'formatter': 'verbose',
#         },
#         'error_file': {
#             'level': 'ERROR',
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': '/var/log/django/error.log',
#             'maxBytes': 1024 * 1024 * 10,
#             'backupCount': 5,
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console', 'file'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#         'django.request': {
#             'handlers': ['error_file', 'console'],
#             'level': 'ERROR',
#             'propagate': False,
#         },
#         'firstapp': {
#             'handlers': ['console', 'file'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'INFO',
#     },
# }

# # Default primary key field type
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# # ============================================================
# # SESSION CONFIGURATION
# # ============================================================

# SESSION_COOKIE_AGE = 86400  # 24 hours
# SESSION_SAVE_EVERY_REQUEST = False
# SESSION_COOKIE_HTTPONLY = True
# SESSION_COOKIE_SAMESITE = 'Lax'

# # ============================================================
# # CACHES
# # ============================================================

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'unique-snowflake',
#         'OPTIONS': {
#             'MAX_ENTRIES': 1000
#         }
#     }
# }










# JAYDENNNNNNNNNNNNNNNNNNNNNNNNN

"""
Django settings for WinnieChO project.
PRODUCTION CONFIGURATION WITH EFS FOR SHARED MEDIA
"""
import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'your-fallback-secret-key')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS for ALB
ALLOWED_HOSTS = ['*']

# Use X-Forwarded-Host header from ALB
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'firstapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

USE_RDS = os.getenv('USE_RDS', 'False') == 'True'

if not USE_RDS:
    # LOCAL DEVELOPMENT
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAMEl', 'winniecho'),
            'USER': os.getenv('DB_USERl', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORDl', ''),
            'HOST': os.getenv('DB_HOSTl', 'localhost'),
            'PORT': os.getenv('DB_PORTl', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
        }
    }
else:
    # AWS RDS (PRODUCTION)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'winniedb'),
            'USER': os.getenv('DB_USER', 'admin'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
                'connect_timeout': 10,
            },
            'CONN_MAX_AGE': 60,
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

# ============================================================
# EFS CONFIGURATION FOR SHARED MEDIA/STATIC FILES
# ============================================================

# ✅ EFS mount point (symlinks created by user-data script)
EFS_AVAILABLE = os.path.islink('/opt/winniecho/media') or os.path.ismount('/mnt/efs')

if EFS_AVAILABLE:
    # ✅ Use symlinked directories (points to EFS)
    MEDIA_ROOT = str(BASE_DIR / 'media')  # Symlink to /mnt/efs/media
    STATIC_ROOT = str(BASE_DIR / 'staticfiles')  # Symlink to /mnt/efs/staticfiles
    print(f"✓ Using EFS storage via symlinks")
    print(f"  MEDIA_ROOT: {MEDIA_ROOT} -> {os.readlink(MEDIA_ROOT) if os.path.islink(MEDIA_ROOT) else 'not a link'}")
else:
    # Fallback to local storage
    MEDIA_ROOT = str(BASE_DIR / 'media')
    STATIC_ROOT = str(BASE_DIR / 'staticfiles')
    print("⚠ Using local storage (EFS not detected)")

# Media and static URLs
MEDIA_URL = '/media/'
STATIC_URL = '/static/'

# Static files directories
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Whitenoise for efficient static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================================
# FILE UPLOAD SETTINGS (OPTIMIZED FOR EFS)
# ============================================================

# Increased file upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Use temporary file uploads (better for EFS)
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# Temporary file upload directory
FILE_UPLOAD_TEMP_DIR = '/tmp'

# ============================================================
# AUTHENTICATION
# ============================================================

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

# Google OAuth
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_OAUTH2_SECRET')
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
    'firstapp.pipeline.create_user_profile',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# ============================================================
# PAYMENT GATEWAYS
# ============================================================

PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')

STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# ============================================================
# EMAIL & NOTIFICATIONS
# ============================================================

ADMIN_EMAIL = 'winniechoofficial@gmail.com'
USE_SNS_NOTIFICATIONS = False  # ✅ Changed to False to use SMTP

SITE_URL = os.getenv('SITE_URL', 'http://winniecho-alb-1659460228.us-east-1.elb.amazonaws.com/')

AWS_SNS_REGION_NAME = AWS_REGION
AWS_SNS_TOPIC_ARN = os.getenv('AWS_SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:729466559172:winniecho-alerts')

# ✅ ALWAYS USE SMTP (simpler than SNS)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ============================================================
# GEMINI AI
# ============================================================

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    except Exception as e:
        print(f"Gemini AI configuration error: {e}")
        GEMINI_AVAILABLE = False
else:
    GEMINI_AVAILABLE = False

# ============================================================
# SECURITY SETTINGS
# ============================================================

if not DEBUG:
    # Don't force HTTPS (ALB handles it)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    
    # Don't use HSTS (ALB handles it)
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# CSRF Trusted Origins for ALB
CSRF_TRUSTED_ORIGINS = [
    'http://winniecho-alb-1659460228.us-east-1.elb.amazonaws.com',
    'https://winniecho-alb-1659460228.us-east-1.elb.amazonaws.com',
]

# ============================================================
# LOGGING
# ============================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/error.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'firstapp': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# SESSION CONFIGURATION
# ============================================================

SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================================
# CACHES
# ============================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}