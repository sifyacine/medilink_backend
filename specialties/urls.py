"""
URL configuration for specialties app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from specialties.views import SpecialtyViewSet, DoctorSpecialtyViewSet

app_name = 'specialties'

router = DefaultRouter()
# Register specific routes BEFORE the catch-all empty route
router.register(r'doctor-specialties', DoctorSpecialtyViewSet, basename='doctor-specialty')
router.register(r'', SpecialtyViewSet, basename='specialty')

urlpatterns = [
    path('', include(router.urls)),
]
