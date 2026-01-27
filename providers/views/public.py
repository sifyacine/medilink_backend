"""
Public provider profile views.
"""
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny

from providers.models import Provider
from providers.serializers.provider import ProviderPublicSerializer
from common.enums import ProviderStatus


class PublicProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public provider profiles endpoint.
    Accessible to everyone (authenticated and unauthenticated).
    Only shows verified providers.
    """
    queryset = Provider.objects.filter(status=ProviderStatus.APPROVED).select_related('user')
    serializer_class = ProviderPublicSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['provider_type']
    search_fields = ['user__email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
