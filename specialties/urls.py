"""
URL configuration for specialties app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from specialties.views import SpecialtyViewSet, DoctorSpecialtyViewSet

app_name = 'specialties'

router = DefaultRouter()
router.register(r'', SpecialtyViewSet, basename='specialty')
router.register(r'doctor-specialties', DoctorSpecialtyViewSet, basename='doctor-specialty')

urlpatterns = [
    path('', include(router.urls)),
]
