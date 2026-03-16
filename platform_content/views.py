"""
Views for platform_content app.

Admin views  – full CRUD, requires IsAuthenticated + IsContentEditor sub-role.
Public views – read-only, AllowAny, returns only active/published content.
"""
from django.db import models
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from platform_content.models import (
    LandingPageSection,
    PlatformAnnouncement,
    FAQ,
    BlogPost,
    ContactInfo,
    PlatformSocialLink,
)
from platform_content.serializers import (
    AdminLandingPageSectionSerializer,
    AdminPlatformAnnouncementSerializer,
    AdminFAQSerializer,
    AdminBlogPostSerializer,
    AdminContactInfoSerializer,
    AdminPlatformSocialLinkSerializer,
    PublicLandingPageSectionSerializer,
    PublicPlatformAnnouncementSerializer,
    PublicFAQSerializer,
    PublicBlogPostSerializer,
    PublicContactInfoSerializer,
    PublicPlatformSocialLinkSerializer,
)
from admins.permissions import IsContentEditor


# ---------------------------------------------------------------------------
# Admin ViewSets
# ---------------------------------------------------------------------------

class AdminLandingPageSectionViewSet(viewsets.ModelViewSet):
    """
    CRUD for landing page sections.
    GET/POST /api/admin/platform/sections/
    GET/PATCH/PUT/DELETE /api/admin/platform/sections/{id}/
    """
    queryset = LandingPageSection.objects.all()
    serializer_class = AdminLandingPageSectionSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['section_key', 'title_en']
    ordering_fields = ['display_order', 'updated_at']

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)


class AdminPlatformAnnouncementViewSet(viewsets.ModelViewSet):
    """
    CRUD for platform announcements.
    GET/POST /api/admin/platform/announcements/
    """
    queryset = PlatformAnnouncement.objects.all()
    serializer_class = AdminPlatformAnnouncementSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['announcement_type', 'target_audience', 'is_active']
    search_fields = ['title_en']
    ordering_fields = ['created_at', 'starts_at', 'ends_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdminFAQViewSet(viewsets.ModelViewSet):
    """
    CRUD for FAQs.
    GET/POST /api/admin/platform/faqs/
    """
    queryset = FAQ.objects.all()
    serializer_class = AdminFAQSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['question_en', 'answer_en']
    ordering_fields = ['display_order', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdminBlogPostViewSet(viewsets.ModelViewSet):
    """
    CRUD + publish action for blog posts.
    POST /api/admin/platform/posts/{id}/publish/
    """
    queryset = BlogPost.objects.all()
    serializer_class = AdminBlogPostSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title_en', 'tags', 'slug']
    ordering_fields = ['created_at', 'published_at']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Mark a DRAFT blog post as PUBLISHED."""
        post = self.get_object()
        if post.status == BlogPost.PostStatus.PUBLISHED:
            return Response(
                {'error': 'Post is already published.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        post.publish()
        return Response(
            {'message': 'Blog post published.', 'published_at': post.published_at},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Move a published post to ARCHIVED."""
        post = self.get_object()
        if post.status == BlogPost.PostStatus.ARCHIVED:
            return Response(
                {'error': 'Post is already archived.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        post.status = BlogPost.PostStatus.ARCHIVED
        post.save(update_fields=['status', 'updated_at'])
        return Response({'message': 'Blog post archived.'}, status=status.HTTP_200_OK)


class AdminContactInfoView(generics.RetrieveUpdateAPIView):
    """
    Singleton contact info — always operates on pk=1.
    GET/PATCH /api/admin/platform/contact/
    """
    serializer_class = AdminContactInfoSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]

    def get_object(self):
        obj, _ = ContactInfo.objects.get_or_create(pk=1)
        return obj

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class AdminPlatformSocialLinkViewSet(viewsets.ModelViewSet):
    """
    CRUD for platform social media links.
    GET/POST /api/admin/platform/social-links/
    """
    queryset = PlatformSocialLink.objects.all()
    serializer_class = AdminPlatformSocialLinkSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['platform', 'is_active']
    ordering_fields = ['display_order']


# ---------------------------------------------------------------------------
# Public ViewSets / Views  (AllowAny, read-only, active content only)
# ---------------------------------------------------------------------------

class PublicLandingPageSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only landing page sections.
    GET /api/platform/sections/
    GET /api/platform/sections/{section_key}/   (lookup by section_key)
    """
    queryset = LandingPageSection.objects.filter(is_active=True).order_by('display_order')
    serializer_class = PublicLandingPageSectionSerializer
    permission_classes = [AllowAny]
    lookup_field = 'section_key'


class PublicPlatformAnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public active announcements, optionally filtered by audience.
    GET /api/platform/announcements/?audience=PATIENTS
    """
    permission_classes = [AllowAny]
    serializer_class = PublicPlatformAnnouncementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['target_audience', 'announcement_type']

    def get_queryset(self):
        from django.utils import timezone
        now = timezone.now()
        return PlatformAnnouncement.objects.filter(
            is_active=True,
        ).filter(
            models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=now)
        ).filter(
            models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now)
        )


class PublicFAQViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public FAQs filtered by active flag.
    GET /api/platform/faqs/
    GET /api/platform/faqs/?category=Patients
    """
    queryset = FAQ.objects.filter(is_active=True).order_by('display_order')
    serializer_class = PublicFAQSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category']
    search_fields = ['question_en', 'question_ar', 'question_fr']


class PublicBlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public published blog posts.
    GET /api/platform/posts/
    GET /api/platform/posts/{slug}/
    """
    queryset = BlogPost.objects.filter(status=BlogPost.PostStatus.PUBLISHED).order_by('-published_at')
    serializer_class = PublicBlogPostSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [SearchFilter]
    search_fields = ['title_en', 'tags']


class PublicContactInfoView(generics.RetrieveAPIView):
    """
    Public contact information (read-only).
    GET /api/platform/contact/
    """
    serializer_class = PublicContactInfoSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        obj, _ = ContactInfo.objects.get_or_create(pk=1)
        return obj


class PublicPlatformSocialLinkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public active platform social links.
    GET /api/platform/social-links/
    """
    queryset = PlatformSocialLink.objects.filter(is_active=True).order_by('display_order')
    serializer_class = PublicPlatformSocialLinkSerializer
    permission_classes = [AllowAny]
