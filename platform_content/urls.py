"""
URL configuration for platform_content app.

Two separate URL modules:
  admin_urls  – write endpoints for content editors (/api/admin/platform/...)
  public_urls – read-only endpoints for the public site (/api/platform/...)

Both are imported from core/urls.py.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from platform_content.views import (
    # Admin views
    AdminLandingPageSectionViewSet,
    AdminPlatformAnnouncementViewSet,
    AdminFAQViewSet,
    AdminBlogPostViewSet,
    AdminContactInfoView,
    AdminPlatformSocialLinkViewSet,
    # Public views
    PublicLandingPageSectionViewSet,
    PublicPlatformAnnouncementViewSet,
    PublicFAQViewSet,
    PublicBlogPostViewSet,
    PublicContactInfoView,
    PublicPlatformSocialLinkViewSet,
)

# ---------------------------------------------------------------------------
# Admin router
# ---------------------------------------------------------------------------
admin_router = DefaultRouter()
admin_router.register('sections', AdminLandingPageSectionViewSet, basename='admin-landing-sections')
admin_router.register('announcements', AdminPlatformAnnouncementViewSet, basename='admin-announcements')
admin_router.register('faqs', AdminFAQViewSet, basename='admin-faqs')
admin_router.register('posts', AdminBlogPostViewSet, basename='admin-blog-posts')
admin_router.register('social-links', AdminPlatformSocialLinkViewSet, basename='admin-social-links')

admin_urlpatterns = [
    path('', include(admin_router.urls)),
    path('contact/', AdminContactInfoView.as_view(), name='admin-contact-info'),
]

# ---------------------------------------------------------------------------
# Public router
# ---------------------------------------------------------------------------
public_router = DefaultRouter()
public_router.register('sections', PublicLandingPageSectionViewSet, basename='public-landing-sections')
public_router.register('announcements', PublicPlatformAnnouncementViewSet, basename='public-announcements')
public_router.register('faqs', PublicFAQViewSet, basename='public-faqs')
public_router.register('posts', PublicBlogPostViewSet, basename='public-blog-posts')
public_router.register('social-links', PublicPlatformSocialLinkViewSet, basename='public-social-links')

public_urlpatterns = [
    path('', include(public_router.urls)),
    path('contact/', PublicContactInfoView.as_view(), name='public-contact-info'),
]
