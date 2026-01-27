"""
URL configuration for admins app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from admins.views import AdminProviderViewSet

app_name = 'admins'

# Router for viewset
router = DefaultRouter()
router.register(r'providers', AdminProviderViewSet, basename='admin-provider')

urlpatterns = [
    path('', include(router.urls)),
]
