"""
Admin views for managing social media links across any entity (providers, platform, etc.).
"""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from social_media.models import SocialMediaLink
from social_media.serializers import SocialMediaLinkSerializer
from admins.permissions import IsAdmin


class AdminSocialMediaLinkViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD for social media links attached to any entity.

    GET    /api/admin/social-links/              - List all social links
    GET    /api/admin/social-links/?provider_id=1 - Filter by provider
    POST   /api/admin/social-links/              - Create link for any entity
    GET    /api/admin/social-links/{id}/         - Link detail
    PATCH  /api/admin/social-links/{id}/         - Update link
    DELETE /api/admin/social-links/{id}/         - Delete link

    To target a provider, pass content_type (provider content type id) and
    object_id (provider pk) in the POST body. Alternatively use the
    ?provider_id= query param on GET to filter.
    """
    serializer_class = SocialMediaLinkSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['platform', 'is_visible']
    ordering_fields = ['display_order', 'platform', 'created_at']
    ordering = ['display_order', 'platform']

    def get_queryset(self):
        qs = SocialMediaLink.objects.select_related('content_type').all()

        provider_id = self.request.query_params.get('provider_id')
        if provider_id:
            from providers.models import Provider
            provider_ct = ContentType.objects.get_for_model(Provider)
            qs = qs.filter(content_type=provider_ct, object_id=provider_id)

        content_type_id = self.request.query_params.get('content_type_id')
        object_id = self.request.query_params.get('object_id')
        if content_type_id and object_id:
            qs = qs.filter(content_type_id=content_type_id, object_id=object_id)

        return qs

    def perform_create(self, serializer):
        """
        Allow admins to create a link for any entity.
        content_type and object_id must be provided in the request body.
        """
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {'message': 'Social media link deleted.'},
            status=status.HTTP_200_OK,
        )
