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
from admins.serializers.provider_review import (
    ProviderListSerializer,
    AdminProviderDetailSerializer,
    ProviderRefuseSerializer,
    ProviderStatusHistorySerializer,
)
from common.enums import ProviderStatus
from providers.services import approve_provider, refuse_provider
from admins.services import suspend_provider, restore_provider, get_client_ip
from admins.permissions import IsAdmin


class AdminProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin viewset for managing provider verification and oversight.

    GET  /api/admin/providers/                    - List all providers (filterable)
    GET  /api/admin/providers/{id}/               - Full provider detail
    POST /api/admin/providers/{id}/approve/       - Approve provider
    POST /api/admin/providers/{id}/refuse/        - Refuse provider (requires reason)
    POST /api/admin/providers/{id}/suspend/       - Suspend approved provider
    POST /api/admin/providers/{id}/restore/       - Restore suspended provider
    GET  /api/admin/providers/{id}/status-history/ - Full status change audit trail
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'provider_type']
    search_fields = [
        'user__email',
        'doctor_profile__first_name',
        'doctor_profile__last_name',
        'nurse_profile__first_name',
        'nurse_profile__last_name',
        'clinic_profile__clinic_name',
        'laboratory_profile__lab_name',
        'seller_profile__business_name',
        'vtc_profile__company_name',
    ]
    ordering_fields = ['created_at', 'approved_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Provider.objects.select_related(
            'user',
            'approved_by',
            'doctor_profile',
            'nurse_profile',
            'clinic_profile',
            'laboratory_profile',
            'seller_profile',
            'vtc_profile',
        ).all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ProviderListSerializer
        return AdminProviderDetailSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a pending or refused provider."""
        provider = self.get_object()
        if provider.status == ProviderStatus.APPROVED:
            return Response(
                {'error': 'Provider is already approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        approve_provider(provider, request.user)
        provider.refresh_from_db()
        return Response(
            {'message': 'Provider approved successfully.', 'provider': AdminProviderDetailSerializer(provider, context={'request': request}).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Legacy alias for approve."""
        return self.approve(request, pk=pk)

    @action(detail=True, methods=['post'])
    def refuse(self, request, pk=None):
        """
        Refuse a provider. Requires a reason of at least 10 characters.

        Body: {"reason": "Incomplete documentation provided"}
        """
        provider = self.get_object()
        if provider.status == ProviderStatus.REFUSED:
            return Response(
                {'error': 'Provider is already refused.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ProviderRefuseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        refuse_provider(provider, serializer.validated_data['reason'], request.user)
        provider.refresh_from_db()
        return Response(
            {'message': 'Provider refused.', 'provider': AdminProviderDetailSerializer(provider, context={'request': request}).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """
        Suspend an approved provider. Also suspends their user account.

        Body: {"reason": "..."} (optional)
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
        return Response(
            {'message': 'Provider suspended.', 'provider': AdminProviderDetailSerializer(provider, context={'request': request}).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a suspended provider back to APPROVED and re-activate their account."""
        provider = self.get_object()
        if provider.status != ProviderStatus.SUSPENDED:
            return Response(
                {'error': 'Only suspended providers can be restored.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ip = get_client_ip(request)
        restore_provider(provider, request.user, ip)
        provider.refresh_from_db()
        return Response(
            {'message': 'Provider restored.', 'provider': AdminProviderDetailSerializer(provider, context={'request': request}).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'], url_path='status-history')
    def status_history(self, request, pk=None):
        """
        Return the full audit trail of status changes for a provider.

        GET /api/admin/providers/{id}/status-history/
        """
        provider = self.get_object()
        history = provider.status_history.select_related('changed_by').order_by('-created_at')
        serializer = ProviderStatusHistorySerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
