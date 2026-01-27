"""
URL configuration for services app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from services.views import ServiceViewSet, DoctorServiceViewSet, NurseServiceViewSet

app_name = 'services'

router = DefaultRouter()
router.register(r'', ServiceViewSet, basename='service')
router.register(r'doctor-services', DoctorServiceViewSet, basename='doctor-service')
router.register(r'nurse-services', NurseServiceViewSet, basename='nurse-service')

urlpatterns = [
    path('', include(router.urls)),
]
