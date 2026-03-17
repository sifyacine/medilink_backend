"""
Admin views for patient record management.

Endpoints:
  GET  /api/admin/patients/            List all PatientRecords
  GET  /api/admin/patients/{id}/       Detail
  POST /api/admin/patients/{id}/suspend/   Suspend linked user account
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admins.permissions import IsAdmin
from admins.serializers.patients import AdminPatientDetailSerializer, AdminPatientListSerializer
from admins.services import get_client_ip, suspend_user
from patients.models import PatientRecord


class AdminPatientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin viewset for viewing and managing PatientRecord objects.

    The viewset is ReadOnly â€” patient records are never directly deleted
    by admins (use soft_delete on the model instead).

    Additional action:
        suspend/ â€” suspend the linked User account if one exists.
    """

    queryset = PatientRecord.objects.filter(is_deleted=False).select_related(
        'linked_user', 'created_by_provider__user'
    ).prefetch_related('provider_access').order_by('-created_at')

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'city', 'gender', 'blood_type']
    search_fields = [
        'first_name', 'last_name', 'email',
        'patient_unique_id', 'phone_number', 'national_id',
    ]
    ordering_fields = ['created_at', 'last_name', 'city']
    ordering = ['-created_at']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminPatientListSerializer
        return AdminPatientDetailSerializer

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        """POST /api/admin/patients/{id}/suspend/ â€” suspend linked user account."""
        record = self.get_object()

        if not record.linked_user:
            return Response(
                {'error': 'This patient record has no linked user account.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = record.linked_user
        if user.account_status == 'SUSPENDED':
            return Response(
                {'error': 'Linked user account is already suspended.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get('reason', '')
        suspend_user(user, request.user, reason=reason, ip=get_client_ip(request))
        return Response({'message': 'Patient account suspended successfully.'})

