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

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition

INSTALLED_APPS = [
    # django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',  # Token authentication
    'django_filters',  # For filtering
    'corsheaders',
    # 'allauth.socialaccount.providers.google',  # Uncomment when needed
    # 'allauth.socialaccount.providers.facebook',  # Uncomment when needed
    
    # dj-rest-auth
    'dj_rest_auth',
    'dj_rest_auth.registration',
    
    # Local apps
    'accounts',
    'providers',
    'admins',
    'common',
    'address',
    'services',
    'specialties',
    'social_media',
    'medical_record',
]

SITE_ID = 1

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=True)  # Set to False in production
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',  # React/Next.js frontend
    'http://localhost:8080',  # Flutter web
])

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

# Media files (user-uploaded: profile images, documents, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
