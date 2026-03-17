"""
Admin views for provider verification workflow.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from providers.models import Provider
from providers.serializers.provider import ProviderDetailSerializer
from admins.serializers.provider_review import (
    ProviderListSerializer,
    ProviderRefuseSerializer,
)
from common.permissions import IsAdmin
from common.enums import ProviderStatus
from providers.services import approve_provider, refuse_provider
from admins.services import suspend_provider, restore_provider, get_client_ip
from admins.permissions import IsAdmin


class AdminProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin viewset for managing provider verification.
    
    GET /api/admin/providers/ - List all providers
    GET /api/admin/providers/?status=PENDING - Filter by status
    GET /api/admin/providers/{id}/ - Get provider details
    POST /api/admin/providers/{id}/approve/ - Approve a provider
    POST /api/admin/providers/{id}/verify/ - Legacy: Approve a provider (use approve)
    POST /api/admin/providers/{id}/refuse/ - Refuse a provider
    
    Security: Only admins can access. Providers cannot access other providers' data.
    """
    queryset = Provider.objects.all().select_related('user', 'approved_by', 'verified_by')
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_queryset(self):
        """
        Return all providers (admin-only access).
        
        Providers cannot access this endpoint due to IsAdmin permission.
        This ensures providers cannot query other providers' records.
        """
        return super().get_queryset()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'provider_type']
    search_fields = ['user__email']
    ordering_fields = ['created_at', 'approved_at', 'verified_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProviderListSerializer
        return ProviderDetailSerializer
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify a provider.
        
        POST /api/admin/providers/{id}/verify/
        
        Headers:
        Authorization: Token abc123...
        
        Response:
        {
            "message": "Provider verified successfully.",
            "provider": {
                "id": 1,
                "email": "doctor@example.com",
                "status": "VERIFIED",
                "verified_at": "2026-01-26T10:00:00Z",
                ...
            }
        }
        """
        provider = self.get_object()
        
        if provider.status == ProviderStatus.VERIFIED:
            return Response(
                {'error': 'Provider is already verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approve_provider(provider, request.user)
        provider.refresh_from_db()
        
        serializer = ProviderDetailSerializer(provider)
        return Response({
            'message': 'Provider approved successfully.',
            'provider': serializer.data,
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def refuse(self, request, pk=None):
        """
        Refuse a provider (requires reason).
        
        POST /api/admin/providers/{id}/refuse/
        
        Headers:
        Authorization: Token abc123...
        
        Request body:
        {
            "reason": "Incomplete documentation provided"
        }
        
        Response:
        {
            "message": "Provider refused successfully.",
            "provider": {
                "id": 1,
                "email": "doctor@example.com",
                "status": "REFUSED",
                "refusal_reason": "Incomplete documentation provided",
                ...
            }
        }
        """
        provider = self.get_object()
        
        if provider.status == ProviderStatus.REFUSED:
            return Response(
                {'error': 'Provider is already refused.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProviderRefuseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        refuse_provider(provider, serializer.validated_data['reason'], request.user)
        
        provider.refresh_from_db()
        detail_serializer = ProviderDetailSerializer(provider)
        return Response({
            'message': 'Provider refused successfully.',
            'provider': detail_serializer.data,
        }, status=status.HTTP_200_OK)

        @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsModerator])
        def suspend(self, request, pk=None):
            """
            Suspend an approved provider.

            POST /api/admin/providers/{id}/suspend/
            Body: {"reason": "..."}  (optional)
            """
            provider = self.get_object()
            if provider.status == ProviderStatus.SUSPENDED:
                return Response(
                    {'error': 'Provider is already suspended.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            reason = request.data.get('reason', '')
            ip = get_client_ip(request)
            suspend_provider(provider, request.user, reason, ip)
            provider.refresh_from_db()
            serializer = ProviderDetailSerializer(provider)
            return Response(
                {'message': 'Provider suspended successfully.', 'provider': serializer.data},
                status=status.HTTP_200_OK,
            )

        @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsModerator])
        def restore(self, request, pk=None):
            """
            Restore a suspended provider back to APPROVED.

            POST /api/admin/providers/{id}/restore/
            """
            provider = self.get_object()
            if provider.status != ProviderStatus.SUSPENDED:
                return Response(
                    {'error': 'Only suspended providers can be restored.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ip = get_client_ip(request)
            restore_provider(provider, request.user, ip)
            provider.refresh_from_db()
            serializer = ProviderDetailSerializer(provider)
            return Response(
                {'message': 'Provider restored successfully.', 'provider': serializer.data},
                status=status.HTTP_200_OK,
            )

