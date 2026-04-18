"""URL configuration for providers app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from providers.views.status import provider_status
from providers.views.profile import provider_profile
from providers.views.public import PublicProviderViewSet
from providers.views.clinic import ClinicViewSet, ClinicProfileView
from providers.views.laboratory import LaboratoryViewSet
from providers.views.seller import SellerViewSet
from providers.views.vtc import VTCViewSet
from providers.views.nurse_location import nurse_location, nurse_location_toggle

app_name = 'providers'

# Router for viewsets
router = DefaultRouter()
router.register(r'public', PublicProviderViewSet, basename='provider-public')
router.register(r'clinic', ClinicViewSet, basename='clinic')
router.register(r'laboratory', LaboratoryViewSet, basename='laboratory')
router.register(r'seller', SellerViewSet, basename='seller')
router.register(r'vtc', VTCViewSet, basename='vtc')

urlpatterns = [
    # Provider status endpoint (for all provider types)
    path('status/', provider_status, name='provider-status'),

    # Provider profile endpoint (for all provider types - doctors, nurses, etc.)
    path('profile/', provider_profile, name='provider-profile'),

    # Authenticated clinic provider profile (no ID required)
    path('clinic/', ClinicProfileView.as_view(), name='clinic-profile'),

    # Nurse location endpoints
    path('nurse/location/', nurse_location, name='nurse-location'),
    path('nurse/location/toggle/', nurse_location_toggle, name='nurse-location-toggle'),

    # Include router URLs
    path('', include(router.urls)),
]
