"""
URL configuration for social_media app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from social_media.views import SocialMediaLinkViewSet

app_name = 'social_media'

router = DefaultRouter()
router.register(r'', SocialMediaLinkViewSet, basename='social-link')

urlpatterns = [
    path('', include(router.urls)),
]
