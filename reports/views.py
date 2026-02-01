"""Views for the reports app."""
from datetime import timedelta
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from reports.models import (
    Report, ReportAggregate, UserBan,
    ReportStatus, ModeratorAction
)
from reports.serializers import (
    ReportSerializer, ReportCreateSerializer, ReportListSerializer,
    ReportActionSerializer, ReportAggregateSerializer,
    UserBanSerializer, UserBanCreateSerializer
)
from reports.permissions import IsAdminUser, IsReporterOrAdmin, CanCreateReport


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reports.
    
    Endpoints:
    - GET /reports/ - List reports (admin: all, user: own reports)
    - POST /reports/ - Create a new report
    - GET /reports/{id}/ - Get report details
    - POST /reports/{id}/action/ - Take action on report (admin only)
    - GET /reports/pending/ - List pending reports (admin only)
    - GET /reports/my-reports/ - List user's own reports
    """
    permission_classes = [IsAuthenticated, IsReporterOrAdmin]
    
    def get_queryset(self):
        """Filter reports based on user role."""
        user = self.request.user
        
        # Admin sees all reports
        if user.is_staff or user.is_superuser:
            queryset = Report.objects.all()
        else:
            # Regular users only see their own reports
            queryset = Report.objects.filter(reporter=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by reason
        reason = self.request.query_params.get('reason')
        if reason:
            queryset = queryset.filter(reason=reason)
        
        # Filter by target
        target_type = self.request.query_params.get('target_type')
        target_id = self.request.query_params.get('target_id')
        
        if target_type and target_id:
            try:
                content_type = ContentType.objects.get(model=target_type.lower())
                queryset = queryset.filter(
                    reported_content_type=content_type,
                    reported_object_id=target_id
                )
            except ContentType.DoesNotExist:
                queryset = queryset.none()
        
        return queryset.select_related(
            'reporter', 'reported_content_type', 'reported_user', 'reviewed_by'
        ).order_by('-priority', '-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        if self.action == 'list':
            return ReportListSerializer
        return ReportSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def take_action(self, request, pk=None):
        """Take moderator action on a report."""
        report = self.get_object()
        serializer = ReportActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        ban_duration = serializer.validated_data.get('ban_duration_days')
        
        if action_type == 'dismiss':
            report.dismiss(reviewer=request.user, notes=notes)
            return Response({'message': 'Report dismissed.'})
        
        elif action_type == 'warn':
            report.take_action(
                reviewer=request.user,
                action=ModeratorAction.WARNING_SENT,
                notes=notes
            )
            # TODO: Send warning notification to reported user
            return Response({'message': 'Warning recorded.'})
        
        elif action_type == 'hide':
            report.take_action(
                reviewer=request.user,
                action=ModeratorAction.CONTENT_HIDDEN,
                notes=notes
            )
            return Response({'message': 'Content hidden.'})
        
        elif action_type == 'suspend':
            if not report.reported_user:
                return Response(
                    {'error': 'No user associated with this report.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create temporary ban
            expires_at = timezone.now() + timedelta(days=ban_duration or 7)
            UserBan.objects.create(
                user=report.reported_user,
                related_report=report,
                reason=notes or f'Suspended due to report: {report.reason}',
                is_permanent=False,
                expires_at=expires_at,
                banned_by=request.user
            )
            
            report.take_action(
                reviewer=request.user,
                action=ModeratorAction.USER_SUSPENDED,
                notes=notes
            )
            
            # Update user status
            from common.enums import UserAccountStatus
            report.reported_user.account_status = UserAccountStatus.SUSPENDED
            report.reported_user.save(update_fields=['account_status'])
            
            return Response({'message': f'User suspended until {expires_at}.'})
        
        elif action_type == 'ban':
            if not report.reported_user:
                return Response(
                    {'error': 'No user associated with this report.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create permanent ban
            UserBan.objects.create(
                user=report.reported_user,
                related_report=report,
                reason=notes or f'Banned due to report: {report.reason}',
                is_permanent=True,
                banned_by=request.user
            )
            
            report.take_action(
                reviewer=request.user,
                action=ModeratorAction.USER_BANNED,
                notes=notes
            )
            
            # Update user status
            from common.enums import UserAccountStatus
            report.reported_user.account_status = UserAccountStatus.DEACTIVATED
            report.reported_user.is_active = False
            report.reported_user.save(update_fields=['account_status', 'is_active'])
            
            return Response({'message': 'User banned permanently.'})
        
        elif action_type == 'escalate':
            report.escalate(reviewer=request.user, notes=notes)
            return Response({'message': 'Report escalated.'})
        
        return Response({'error': 'Unknown action.'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def pending(self, request):
        """List pending reports for admin review."""
        queryset = Report.objects.filter(
            status=ReportStatus.PENDING
        ).select_related(
            'reporter', 'reported_content_type', 'reported_user'
        ).order_by('-priority', '-created_at')
        
        serializer = ReportListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_reports(self, request):
        """List authenticated user's own reports."""
        queryset = Report.objects.filter(
            reporter=request.user
        ).order_by('-created_at')
        
        serializer = ReportListSerializer(queryset, many=True)
        return Response(serializer.data)


class ReportAggregateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for report aggregates.
    Admin only.
    """
    queryset = ReportAggregate.objects.all()
    serializer_class = ReportAggregateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Filter by entity type if specified."""
        queryset = ReportAggregate.objects.all()
        
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            try:
                content_type = ContentType.objects.get(model=entity_type.lower())
                queryset = queryset.filter(content_type=content_type)
            except ContentType.DoesNotExist:
                queryset = queryset.none()
        
        # Filter by minimum reports
        min_reports = self.request.query_params.get('min_reports')
        if min_reports:
            queryset = queryset.filter(total_reports__gte=int(min_reports))
        
        return queryset.select_related('content_type').order_by(
            '-pending_reports', '-total_reports'
        )


class UserBanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user bans.
    Admin only.
    """
    queryset = UserBan.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserBanCreateSerializer
        return UserBanSerializer
    
    def get_queryset(self):
        queryset = UserBan.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.select_related('user', 'banned_by', 'lifted_by')
    
    @action(detail=True, methods=['post'])
    def lift(self, request, pk=None):
        """Lift a ban."""
        ban = self.get_object()
        
        if not ban.is_active:
            return Response(
                {'error': 'Ban is already lifted.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        ban.lift(lifted_by=request.user, reason=reason)
        
        # Restore user account status
        from common.enums import UserAccountStatus
        ban.user.account_status = UserAccountStatus.ACTIVE
        ban.user.is_active = True
        ban.user.save(update_fields=['account_status', 'is_active'])
        
        return Response({'message': 'Ban lifted successfully.'})
