"""
Admin view for the AdminActivityLog (read-only).

Endpoints:
  GET /api/admin/logs/       List with filters: action, admin, date_from, date_to
  GET /api/admin/logs/{id}/  Detail
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets

from admins.models import AdminActivityLog
from admins.permissions import IsSupport
from admins.serializers.activity_log import AdminActivityLogSerializer


class AdminActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for admin activity logs.

    Accessible by SUPPORT sub-role and above (SUPER_ADMIN, MODERATOR, SUPPORT).
    CONTENT_EDITOR sub-role cannot access logs.

    Filtering:
        ?action=USER_SUSPEND
        ?admin=<user_id>
        ?date_from=2026-01-01&date_to=2026-03-01  (via search_fields override — use ordering)

    Ordering: -created_at (default)
    """
    queryset = AdminActivityLog.objects.all().select_related(
        'admin', 'content_type'
    ).order_by('-created_at')

    serializer_class = AdminActivityLogSerializer
    permission_classes = [IsAuthenticated, IsSupport]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'admin']
    search_fields = ['object_repr', 'admin__email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
