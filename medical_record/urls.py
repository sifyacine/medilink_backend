"""
URL configuration for medical_record app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from medical_record.views import MedicalRecordViewSet

router = DefaultRouter()
router.register(r'records', MedicalRecordViewSet, basename='medical-record')

app_name = 'medical_record'

urlpatterns = [
    path('', include(router.urls)),
]
