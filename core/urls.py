from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import service worker view for web push notifications
from notifications.views import service_worker
from platform_content.urls import admin_urlpatterns as platform_admin_urls
from platform_content.urls import public_urlpatterns as platform_public_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Firebase Service Worker (MUST be at root for web push to work)
    path('firebase-messaging-sw.js', service_worker, name='firebase_service_worker'),
    
    # Authentication endpoints
    path('api/auth/', include('accounts.urls')),
    
    # Provider endpoints
    path('api/provider/', include('providers.urls')),
    
    # Admin endpoints
    path('api/admin/', include('admins.urls')),
    
    # Specialties endpoints
    path('api/specialties/', include('specialties.urls')),
    
    # Services endpoints
    path('api/services/', include('services.urls')),
    
    # Address endpoints
    path('api/addresses/', include('address.urls')),
    
    # Social media endpoints
    path('api/social-links/', include('social_media.urls')),
    
    # Medical records endpoints
    path('api/medical-records/', include('medical_record.urls')),
    
    # Patient records endpoints (patients without accounts)
    path('api/patients/', include('patients.urls')),
    
    # Notifications endpoints
    path('api/', include('notifications.urls')),
    
    # Appointments endpoints
    path('api/', include('appointments.urls')),
    
    # Prescriptions endpoints
    path('api/', include('prescriptions.urls')),
    
    # On-demand nursing service endpoints
    path('api/nurse-requests/', include('nurse_requests.urls')),
    
    # Reviews and ratings endpoints
    path('api/reviews/', include('reviews.urls')),
    
    # Reports and moderation endpoints
    path('api/reports/', include('reports.urls')),
    
    # Invoices endpoints
    path('api/invoices/', include('invoices.urls')),

    # Platform content – admin write endpoints (CONTENT_EDITOR only)
    path('api/admin/platform/', include(platform_admin_urls)),
    # Platform content – public read-only endpoints
    path('api/platform/', include(platform_public_urls)),

    # django-allauth URLs (for email verification pages if needed)
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    # Serve media files (profile images, documents, etc.) in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
