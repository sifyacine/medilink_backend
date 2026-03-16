import os
from pathlib import Path
import environ



# Initialise django-environ
env = environ.Env(
    # Set default values and casting
    DEBUG=(bool, False),
)
# Read .env file from project root
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list(
    'ALLOWED_HOSTS',
    default=[
        'localhost',
        'localhost:3000',
        'localhost:5173',
        'localhost:8000',
        '127.0.0.1:3000',
        '127.0.0.1:5173',
        '127.0.0.1:8000',
        '127.0.0.1',
        'dzmedilink.netlify.app',
        'dzmedilink.duckdns.org',
    ],
)

# Application definition

INSTALLED_APPS = [
    # Daphne ASGI server (MUST come first for runserver to use ASGI)
    'daphne',

    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'corsheaders',
    'channels',  # WebSocket support

    # allauth (AFTER auth)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # dj-rest-auth
    'dj_rest_auth',
    'dj_rest_auth.registration',

    # Local apps (custom user BEFORE dependents)
    'accounts',          # ⭐ custom user FIRST
    'providers',
    'admins',
    'common',
    'address',
    'services',
    'specialties',
    'social_media',
    'medical_record',
    'patients',  # Patient records without accounts
    'notifications',  # Notification system
    'appointments',  # Appointment scheduling
    'prescriptions',  # Prescription management
    'nurse_requests',  # On-demand nursing services
    'reviews',  # Universal reviews and ratings system
    'reports',  # Universal reporting and moderation system
    'invoices',  # Invoice and payment management
    'platform_content',  # CMS: landing page, blog, FAQs, announcements, etc.
]

# Invoice Settings
MEDILINK_AUTO_INVOICE_APPOINTMENTS = False  # Auto-create invoice on appointment completion
MEDILINK_AUTO_INVOICE_NURSE_REQUESTS = False  # Auto-create invoice on nurse request completion
MEDILINK_AUTO_SEND_INVOICES = False  # Auto-send invoices when created

SITE_ID = 1

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=True)  # Set to False in production
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=[
        'http://localhost:3000',  # React/Next.js frontend
        'http://localhost:8080',  # Flutter web
        'http://localhost:5173',  # Vite dev server
        'http://localhost:8000',  # Local Django (for tools / proxies)
        'https://dzmedilink.netlify.app',  # Deployed frontend
        'http://dzmedilink.duckdns.org',  # Deployed backend HTTP
        'https://dzmedilink.duckdns.org',  # Deployed backend HTTPS
    ],
)

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    # Custom exception handler for consistent API error responses
    'EXCEPTION_HANDLER': 'common.exception_handlers.medilink_exception_handler',
}

# dj-rest-auth Configuration (Token-based, not JWT)
REST_AUTH = {
    'USE_JWT': False,  # Use token authentication instead
    'TOKEN_MODEL': 'rest_framework.authtoken.models.Token',
    'USER_DETAILS_SERIALIZER': 'accounts.serializers.user.UserSerializer',
    'REGISTER_SERIALIZER': 'accounts.serializers.auth.CustomRegisterSerializer',
}

# Django-allauth Configuration
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Django default
    'allauth.account.auth_backends.AuthenticationBackend',  # django-allauth
]

# django-allauth Configuration for API usage
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # Login with email instead of username
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Disable email verification for API (can enable later)
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False

# Email will be sent as lowercase
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Allow account creation without email verification for API
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'

# Prevent auto-signup on social login (require additional info)
SOCIALACCOUNT_AUTO_SIGNUP = False

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS - must be before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # django-allauth
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='medilink_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='127.0.0.1'),
        'PORT': env('DB_PORT', default='5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static & media files
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"


# Media files (user-uploaded: profile images, documents, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Django Channels Configuration
ASGI_APPLICATION = 'core.asgi.application'

# Channel layers configuration
# Default: In-memory channel layer (for development)
# For production, use Redis channel layer
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# For production with Redis:
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
#         },
#     },
# }

