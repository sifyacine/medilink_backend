"""
Admin views for user management.

Endpoints:
  GET    /api/admin/users/                  List all users (filter: role, account_status)
  GET    /api/admin/users/{id}/             User detail
  PATCH  /api/admin/users/{id}/             Edit basic info
  POST   /api/admin/users/{id}/suspend/     Suspend account
  POST   /api/admin/users/{id}/activate/    Activate account
  POST   /api/admin/users/{id}/deactivate/  Deactivate account
  POST   /api/admin/users/{id}/reset-password/   Send password reset
  GET    /api/admin/users/{id}/activity/    Login + appointment history
"""
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admins.permissions import IsAdmin
from admins.serializers.users import (
    AdminUserDetailSerializer,
    AdminUserListSerializer,
    AdminUserSuspendSerializer,
    AdminUserUpdateSerializer,
)
from admins.services import (
    activate_user,
    deactivate_user,
    get_client_ip,
    send_admin_password_reset,
    suspend_user,
)

User = get_user_model()


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for managing platform users.
    All admins have equal access -- no sub-role restrictions.
    """

    queryset = User.objects.all().select_related(
        'provider_profile', 'patient_record',
    ).order_by('-created_at')

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'account_status']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['created_at', 'last_login', 'email']
    ordering = ['-created_at']

    http_method_names = ['get', 'patch', 'head', 'options']

    def get_permissions(self):
        return [IsAuthenticated(), IsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminUserListSerializer
        if self.action == 'partial_update':
            return AdminUserUpdateSerializer
        return AdminUserDetailSerializer

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        user = self.get_object()
        serializer = AdminUserSuspendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user.account_status == 'SUSPENDED':
            return Response({'error': 'User is already suspended.'}, status=status.HTTP_400_BAD_REQUEST)
        suspend_user(user, request.user, reason=serializer.validated_data.get('reason', ''), ip=get_client_ip(request))
        return Response({'message': 'User suspended successfully.'})

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        user = self.get_object()
        if user.account_status == 'ACTIVE':
            return Response({'error': 'User is already active.'}, status=status.HTTP_400_BAD_REQUEST)
        activate_user(user, request.user, ip=get_client_ip(request))
        return Response({'message': 'User activated successfully.'})

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        user = self.get_object()
        serializer = AdminUserSuspendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user.account_status == 'DEACTIVATED':
            return Response({'error': 'User is already deactivated.'}, status=status.HTTP_400_BAD_REQUEST)
        deactivate_user(user, request.user, reason=serializer.validated_data.get('reason', ''), ip=get_client_ip(request))
        return Response({'message': 'User deactivated successfully.'})

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        send_admin_password_reset(user, request.user, ip=get_client_ip(request))
        return Response({'message': 'Password reset email sent successfully.'})

    @action(detail=True, methods=['get'], url_path='activity')
    def activity(self, request, pk=None):
        user = self.get_object()
        appointment_stats = {}
        try:
            from appointments.models import Appointment
            from django.db.models import Count
            qs = Appointment.objects.filter(patient_user=user)
            stats = qs.values('status').annotate(count=Count('id'))
            appointment_stats = {s['status']: s['count'] for s in stats}
        except Exception:
            pass

        invoice_stats = {}
        try:
            from invoices.models import Invoice
            from django.db.models import Sum
            inv_qs = Invoice.objects.filter(patient=user)
            invoice_stats = {
                'total': inv_qs.count(),
                'paid': inv_qs.filter(status='PAID').count(),
                'total_amount': str(inv_qs.filter(status='PAID').aggregate(t=Sum('total'))['t'] or '0.00'),
            }
        except Exception:
            pass

        return Response({
            'user_id': user.id,
            'email': user.email,
            'last_login': user.last_login,
            'last_login_ip': user.last_login_ip,
            'failed_login_attempts': user.failed_login_attempts,
            'locked_until': user.locked_until,
            'appointment_stats': appointment_stats,
            'invoice_stats': invoice_stats,
        })
