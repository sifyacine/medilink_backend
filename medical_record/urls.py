"""
URL configuration for medical_record app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from medical_record.views import MedicalRecordViewSet, ProviderAccessViewSet

router = DefaultRouter()
router.register(r'records', MedicalRecordViewSet, basename='medical-record')
router.register(r'access', ProviderAccessViewSet, basename='provider-access')

app_name = 'medical_record'

urlpatterns = [
    path('', include(router.urls)),
]
