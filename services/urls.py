"""
URL configuration for services app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from services.views import ServiceViewSet, DoctorServiceViewSet, NurseServiceViewSet

app_name = 'services'

router = DefaultRouter()
# Register specific routes BEFORE the catch-all empty route
router.register(r'doctor-services', DoctorServiceViewSet, basename='doctor-service')
router.register(r'nurse-services', NurseServiceViewSet, basename='nurse-service')
router.register(r'', ServiceViewSet, basename='service')

urlpatterns = [
    path('', include(router.urls)),
]
