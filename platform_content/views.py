"""
Views for platform_content app.

Admin views  – full CRUD, requires IsAuthenticated + IsAdmin.
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
    LegalDocument,
)
from platform_content.serializers import (
    AdminLandingPageSectionSerializer,
    AdminPlatformAnnouncementSerializer,
    AdminFAQSerializer,
    AdminBlogPostSerializer,
    AdminContactInfoSerializer,
    AdminPlatformSocialLinkSerializer,
    AdminLegalDocumentSerializer,
    PublicLandingPageSectionSerializer,
    PublicPlatformAnnouncementSerializer,
    PublicFAQSerializer,
    PublicBlogPostSerializer,
    PublicContactInfoSerializer,
    PublicPlatformSocialLinkSerializer,
    PublicLegalDocumentSerializer,
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
    search_fields = ['title_en', 'title_ar', 'title_fr']
    ordering_fields = ['created_at', 'starts_at', 'ends_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdminFAQViewSet(viewsets.ModelViewSet):
    """
    CRUD + bulk reorder for FAQs.

    GET/POST  /api/admin/platform/faqs/
    GET/PATCH/PUT/DELETE /api/admin/platform/faqs/{id}/
    POST /api/admin/platform/faqs/reorder/
         Body: [{"id": 3, "display_order": 0}, {"id": 1, "display_order": 1}, ...]
    """
    queryset = FAQ.objects.all()
    serializer_class = AdminFAQSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['question_en', 'question_ar', 'question_fr', 'answer_en']
    ordering_fields = ['display_order', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Bulk-update display_order for multiple FAQs in one request.

        POST /api/admin/platform/faqs/reorder/
        Body: [{"id": 3, "display_order": 0}, {"id": 1, "display_order": 1}]
        """
        items = request.data
        if not isinstance(items, list):
            return Response(
                {'error': 'Expected a list of {id, display_order} objects.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = []
        errors = []
        for item in items:
            faq_id = item.get('id')
            order = item.get('display_order')
            if faq_id is None or order is None:
                errors.append({'item': item, 'error': 'Both id and display_order are required.'})
                continue
            try:
                faq = FAQ.objects.get(pk=faq_id)
                faq.display_order = order
                faq.save(update_fields=['display_order'])
                updated.append(faq_id)
            except FAQ.DoesNotExist:
                errors.append({'item': item, 'error': f'FAQ {faq_id} not found.'})

        return Response(
            {'updated': updated, 'errors': errors},
            status=status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS,
        )


class AdminBlogPostViewSet(viewsets.ModelViewSet):
    """
    CRUD + publish/archive actions for blog posts.
    POST /api/admin/platform/posts/{id}/publish/
    POST /api/admin/platform/posts/{id}/archive/
    """
    queryset = BlogPost.objects.all()
    serializer_class = AdminBlogPostSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title_en', 'title_ar', 'title_fr', 'tags', 'slug']
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
    GET/PATCH/PUT/DELETE /api/admin/platform/social-links/{id}/
    """
    queryset = PlatformSocialLink.objects.all()
    serializer_class = AdminPlatformSocialLinkSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['platform', 'is_active']
    ordering_fields = ['display_order']


class AdminLegalDocumentView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a legal document by its type slug.

    GET  /api/admin/platform/legal/privacy-policy/
    PATCH /api/admin/platform/legal/privacy-policy/

    GET  /api/admin/platform/legal/terms-and-conditions/
    PATCH /api/admin/platform/legal/terms-and-conditions/

    GET  /api/admin/platform/legal/cookie-policy/
    PATCH /api/admin/platform/legal/cookie-policy/

    The record is auto-created on first GET if it doesn't exist yet.
    document_type is read-only — use the URL to select the document.
    """
    serializer_class = AdminLegalDocumentSerializer
    permission_classes = [IsAuthenticated, IsContentEditor]

    # Maps URL slug → DocumentType enum value
    SLUG_TO_TYPE = {
        'privacy-policy':       LegalDocument.DocumentType.PRIVACY_POLICY,
        'terms-and-conditions': LegalDocument.DocumentType.TERMS_AND_CONDITIONS,
        'cookie-policy':        LegalDocument.DocumentType.COOKIE_POLICY,
    }

    def _get_document_type(self):
        slug = self.kwargs.get('doc_type', '')
        doc_type = self.SLUG_TO_TYPE.get(slug)
        if not doc_type:
            from rest_framework.exceptions import NotFound
            raise NotFound(f'Unknown legal document type: "{slug}". '
                           f'Valid options: {list(self.SLUG_TO_TYPE.keys())}')
        return doc_type

    def get_object(self):
        doc_type = self._get_document_type()
        obj, _ = LegalDocument.objects.get_or_create(document_type=doc_type)
        return obj

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# ---------------------------------------------------------------------------
# Public ViewSets / Views  (AllowAny, read-only, active content only)
# ---------------------------------------------------------------------------

class PublicLandingPageSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only landing page sections.
    GET /api/platform/sections/
    GET /api/platform/sections/{section_key}/
    """
    queryset = LandingPageSection.objects.filter(is_active=True).order_by('display_order')
    serializer_class = PublicLandingPageSectionSerializer
    permission_classes = [AllowAny]
    lookup_field = 'section_key'


class PublicPlatformAnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public active announcements, optionally filtered by audience.
    GET /api/platform/announcements/?target_audience=PATIENTS
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
    search_fields = ['title_en', 'title_ar', 'title_fr', 'tags']


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


class PublicLegalDocumentView(generics.RetrieveAPIView):
    """
    Public read-only view for a legal document by type slug.

    GET /api/platform/legal/privacy-policy/
    GET /api/platform/legal/terms-and-conditions/
    GET /api/platform/legal/cookie-policy/

    Returns 404 if the document hasn't been created yet or is inactive.
    """
    serializer_class = PublicLegalDocumentSerializer
    permission_classes = [AllowAny]

    SLUG_TO_TYPE = {
        'privacy-policy':       LegalDocument.DocumentType.PRIVACY_POLICY,
        'terms-and-conditions': LegalDocument.DocumentType.TERMS_AND_CONDITIONS,
        'cookie-policy':        LegalDocument.DocumentType.COOKIE_POLICY,
    }

    def get_object(self):
        slug = self.kwargs.get('doc_type', '')
        doc_type = self.SLUG_TO_TYPE.get(slug)
        if not doc_type:
            from rest_framework.exceptions import NotFound
            raise NotFound(f'Unknown document type: "{slug}".')
        try:
            return LegalDocument.objects.get(document_type=doc_type, is_active=True)
        except LegalDocument.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('This document has not been published yet.')
