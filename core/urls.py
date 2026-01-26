
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication endpoints (django-allauth + dj-rest-auth)
    path('api/v1/auth/', include('dj_rest_auth.urls')),  # login, logout, password reset, etc.
    path('api/v1/auth/register/', include('dj_rest_auth.registration.urls')),  # registration
    
    # django-allauth URLs (for email verification pages)
    path('accounts/', include('allauth.urls')),
    
    # Your app URLs will be added here
    # path('api/v1/patients/', include('apps.patients.urls')),
    # path('api/v1/doctors/', include('apps.doctors.urls')),
    # etc.
]
