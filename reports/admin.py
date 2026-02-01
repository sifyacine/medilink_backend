"""Admin configuration for reports app."""
from django.contrib import admin
from django.utils.html import format_html

from reports.models import Report, ReportAggregate, UserBan, ReportStatus, ModeratorAction


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin interface for Report model."""
    list_display = [
        'id', 'reporter', 'reported_type', 'reason',
        'status_display', 'priority', 'created_at'
    ]
    list_filter = ['status', 'reason', 'priority', 'reported_content_type', 'created_at']
    search_fields = ['reporter__email', 'description', 'reported_user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-priority', '-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Info', {
            'fields': ('id', 'reporter', 'status', 'priority')
        }),
        ('Target', {
            'fields': ('reported_content_type', 'reported_object_id', 'reported_user')
        }),
        ('Details', {
            'fields': ('reason', 'description', 'evidence_image', 'evidence_file')
        }),
        ('Moderation', {
            'fields': ('reviewed_by', 'reviewed_at', 'action_taken', 'action_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def reported_type(self, obj):
        """Display the type of reported object."""
        return obj.reported_content_type.model.title()
    reported_type.short_description = 'Reported Type'
    
    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            'PENDING': 'orange',
            'UNDER_REVIEW': 'blue',
            'ACTION_TAKEN': 'green',
            'DISMISSED': 'gray',
            'ESCALATED': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    actions = ['start_review', 'dismiss_reports', 'escalate_reports']
    
    def start_review(self, request, queryset):
        """Start review on selected reports."""
        count = 0
        for report in queryset.filter(status=ReportStatus.PENDING):
            report.start_review(reviewer=request.user)
            count += 1
        self.message_user(request, f'{count} reports marked as under review.')
    start_review.short_description = 'Start review on selected reports'
    
    def dismiss_reports(self, request, queryset):
        """Dismiss selected reports."""
        count = 0
        for report in queryset.exclude(status=ReportStatus.DISMISSED):
            report.dismiss(reviewer=request.user, notes='Bulk dismissed by admin.')
            count += 1
        self.message_user(request, f'{count} reports dismissed.')
    dismiss_reports.short_description = 'Dismiss selected reports'
    
    def escalate_reports(self, request, queryset):
        """Escalate selected reports."""
        count = 0
        for report in queryset:
            report.escalate(reviewer=request.user)
            count += 1
        self.message_user(request, f'{count} reports escalated.')
    escalate_reports.short_description = 'Escalate selected reports'


@admin.register(ReportAggregate)
class ReportAggregateAdmin(admin.ModelAdmin):
    """Admin interface for ReportAggregate model."""
    list_display = [
        'id', 'content_type', 'object_id',
        'total_reports', 'pending_reports', 'actioned_reports',
        'last_reported_at'
    ]
    list_filter = ['content_type', 'updated_at']
    search_fields = ['object_id']
    readonly_fields = ['id', 'updated_at']
    ordering = ['-total_reports', '-pending_reports']


@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    """Admin interface for UserBan model."""
    list_display = [
        'id', 'user', 'is_permanent', 'expires_at',
        'is_active', 'banned_by', 'created_at'
    ]
    list_filter = ['is_active', 'is_permanent', 'created_at']
    search_fields = ['user__email', 'reason', 'banned_by__email']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Ban Info', {
            'fields': ('id', 'user', 'related_report')
        }),
        ('Details', {
            'fields': ('reason', 'is_permanent', 'expires_at')
        }),
        ('Administration', {
            'fields': ('banned_by', 'is_active')
        }),
        ('Lifting', {
            'fields': ('lifted_at', 'lifted_by', 'lift_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['lift_bans']
    
    def lift_bans(self, request, queryset):
        """Lift selected bans."""
        count = 0
        for ban in queryset.filter(is_active=True):
            ban.lift(lifted_by=request.user, reason='Bulk lifted by admin.')
            count += 1
        self.message_user(request, f'{count} bans lifted.')
    lift_bans.short_description = 'Lift selected bans'
