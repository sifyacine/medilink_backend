"""
Public URL configuration for MediLink product catalog.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from admins.views import PublicProductViewSet


app_name = 'public-products'

router = DefaultRouter()
router.register(r'', PublicProductViewSet, basename='public-products')

urlpatterns = [
    path('', include(router.urls)),
]
