"""
URL configuration for medical_records app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from medical_records.views import (
    MedicalRecordViewSet,
    AllergyViewSet,
    ProviderAccessViewSet,
)

app_name = 'medical_records'

router = DefaultRouter()
router.register(r'records', MedicalRecordViewSet, basename='medical-record')
router.register(r'allergies', AllergyViewSet, basename='allergy')
router.register(r'provider-access', ProviderAccessViewSet, basename='provider-access')

urlpatterns = [
    path('', include(router.urls)),
]
