from .base import *  # noqa

# Production-specific overrides
DEBUG = False

# Restrict allowed hosts in production
ALLOWED_HOSTS = env.list(
	'ALLOWED_HOSTS',
	default=[
		'dzmedilink.netlify.app',
		'dzmedilink.duckdns.org',
	],
)

# CORS: be explicit in production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list(
	'CORS_ALLOWED_ORIGINS',
	default=[
		'https://dzmedilink.netlify.app',
		'http://dzmedilink.duckdns.org',
		'http://localhost:3000',
		'http://localhost:5173',
		'http://localhost:8000',
	],
)

# DigitalOcean managed PostgreSQL database configuration
DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': env('DB_NAME', default='defaultdb'),
		'USER': env('DB_USER', default='doadmin'),
		'PASSWORD': env('DB_PASSWORD'),
		'HOST': env('DB_HOST', default='medilink-db-do-user-32042353-0.d.db.ondigitalocean.com'),
		'PORT': env('DB_PORT', default='25060'),
		'OPTIONS': {
			'sslmode': env('DB_SSLMODE', default='require'),
		},
	}
}

# Recommended basic security settings for production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'