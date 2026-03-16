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

from admins.permissions import IsAdmin, IsModerator, IsSupport
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
from common.enums import UserRole

User = get_user_model()


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for managing platform users.

    Security:
        - All actions require IsAuthenticated + IsAdmin.
        - Write actions (suspend/deactivate/update) additionally require IsModerator.
        - SUPPORT-only admins have full read access.
        - An admin cannot suspend or deactivate another SUPER_ADMIN.
    """

    queryset = User.objects.all().select_related(
        'provider_profile', 'patient_record', 'admin_profile'
    ).order_by('-created_at')

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'account_status']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['created_at', 'last_login', 'email']
    ordering = ['-created_at']

    http_method_names = ['get', 'patch', 'head', 'options']  # no PUT / DELETE / POST

    def get_permissions(self):
        if self.action in ('partial_update', 'suspend', 'activate', 'deactivate', 'reset_password'):
            return [IsAuthenticated(), IsModerator()]
        return [IsAuthenticated(), IsSupport()]

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminUserListSerializer
        if self.action == 'partial_update':
            return AdminUserUpdateSerializer
        return AdminUserDetailSerializer

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _guard_super_admin(self, target):
        """Prevent any admin from modifying another SUPER_ADMIN."""
        from common.enums import AdminSubRole
        try:
            if (
                target.admin_profile.sub_role == AdminSubRole.SUPER_ADMIN
                and target != self.request.user
            ):
                return Response(
                    {'error': 'Super admin accounts cannot be modified by other admins.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Custom actions
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        """POST /api/admin/users/{id}/suspend/"""
        user = self.get_object()
        guard = self._guard_super_admin(user)
        if guard:
            return guard

        serializer = AdminUserSuspendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if user.account_status == 'SUSPENDED':
            return Response({'error': 'User is already suspended.'}, status=status.HTTP_400_BAD_REQUEST)

        suspend_user(
            user, request.user,
            reason=serializer.validated_data.get('reason', ''),
            ip=get_client_ip(request),
        )
        return Response({'message': 'User suspended successfully.'})

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """POST /api/admin/users/{id}/activate/"""
        user = self.get_object()
        if user.account_status == 'ACTIVE':
            return Response({'error': 'User is already active.'}, status=status.HTTP_400_BAD_REQUEST)

        activate_user(user, request.user, ip=get_client_ip(request))
        return Response({'message': 'User activated successfully.'})

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """POST /api/admin/users/{id}/deactivate/"""
        user = self.get_object()
        guard = self._guard_super_admin(user)
        if guard:
            return guard

        serializer = AdminUserSuspendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if user.account_status == 'DEACTIVATED':
            return Response({'error': 'User is already deactivated.'}, status=status.HTTP_400_BAD_REQUEST)

        deactivate_user(
            user, request.user,
            reason=serializer.validated_data.get('reason', ''),
            ip=get_client_ip(request),
        )
        return Response({'message': 'User deactivated successfully.'})

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """POST /api/admin/users/{id}/reset-password/"""
        user = self.get_object()
        send_admin_password_reset(user, request.user, ip=get_client_ip(request))
        return Response({'message': 'Password reset email sent successfully.'})

    @action(detail=True, methods=['get'], url_path='activity')
    def activity(self, request, pk=None):
        """GET /api/admin/users/{id}/activity/ — login history + appointment stats."""
        user = self.get_object()

        # Appointment stats (if appointments app exists)
        appointment_stats = {}
        try:
            from appointments.models import Appointment
            from django.db.models import Count

            qs = Appointment.objects.filter(patient_user=user)
            stats = qs.values('status').annotate(count=Count('id'))
            appointment_stats = {s['status']: s['count'] for s in stats}
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
        })
