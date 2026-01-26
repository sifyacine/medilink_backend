from .base import *

DEBUG = True

# Use console email backend in development so django-allauth
# email verification links are printed to the terminal instead
# of sending real emails.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'no-reply@medilink.local'