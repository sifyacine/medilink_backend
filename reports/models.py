"""
Generic Reports & Moderation system for the Medilink platform.

This module provides a fully generic reporting system that supports:
- Anyone can report anything (users, content, reviews, etc.)
- Predefined report reasons with custom descriptions
- Admin moderation workflow
- Actions tracking (ban, hide, dismiss, etc.)
- Generic Foreign Key for reported objects

Usage examples:
- Patient reports inappropriate Nurse behavior
- User reports offensive review
- User reports fake doctor profile
- Admin takes action on reports

Architecture decisions:
1. Uses Django's ContentType framework for polymorphic relationships
2. Supports multiple reports for the same target (aggregates for admin view)
3. Tracks admin actions and moderation history
4. Integrates with user account status for banning
"""
import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from accounts.models import User


class ReportReason(models.TextChoices):
    """Predefined report reasons."""
    INAPPROPRIATE_BEHAVIOR = 'INAPPROPRIATE_BEHAVIOR', 'Inappropriate Behavior'
    HARASSMENT = 'HARASSMENT', 'Harassment'
    SPAM = 'SPAM', 'Spam'
    FAKE_PROFILE = 'FAKE_PROFILE', 'Fake Profile'
    SCAM = 'SCAM', 'Scam/Fraud'
    UNPROFESSIONAL = 'UNPROFESSIONAL', 'Unprofessional Conduct'
    SAFETY_CONCERN = 'SAFETY_CONCERN', 'Safety Concern'
    INCORRECT_INFO = 'INCORRECT_INFO', 'Incorrect Information'
    OFFENSIVE_CONTENT = 'OFFENSIVE_CONTENT', 'Offensive Content'
    COPYRIGHT = 'COPYRIGHT', 'Copyright Violation'
    OTHER = 'OTHER', 'Other'


class ReportStatus(models.TextChoices):
    """Report status choices."""
    PENDING = 'PENDING', 'Pending Review'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    ACTION_TAKEN = 'ACTION_TAKEN', 'Action Taken'
    DISMISSED = 'DISMISSED', 'Dismissed'
    ESCALATED = 'ESCALATED', 'Escalated'


class ModeratorAction(models.TextChoices):
    """Actions that can be taken by moderators."""
    NO_ACTION = 'NO_ACTION', 'No Action Required'
    WARNING_SENT = 'WARNING_SENT', 'Warning Sent'
    CONTENT_HIDDEN = 'CONTENT_HIDDEN', 'Content Hidden'
    CONTENT_REMOVED = 'CONTENT_REMOVED', 'Content Removed'
    USER_SUSPENDED = 'USER_SUSPENDED', 'User Suspended'
    USER_BANNED = 'USER_BANNED', 'User Banned'
    PROVIDER_SUSPENDED = 'PROVIDER_SUSPENDED', 'Provider Suspended'
    ESCALATED = 'ESCALATED', 'Escalated to Admin'
    OTHER = 'OTHER', 'Other Action'


class Report(models.Model):
    """
    Generic Report model for moderation.
    
    Supports reporting any model instance with:
    - Predefined reasons
    - Custom description
    - Evidence (image/file)
    - Status tracking
    - Admin action workflow
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Reporter (required)
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_filed',
        help_text='User who filed this report'
    )
    
    # Reported entity (Generic Foreign Key)
    reported_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='reports',
        help_text='Content type of the reported object'
    )
    reported_object_id = models.CharField(
        max_length=255,
        help_text='ID of the reported object (supports UUID and int)'
    )
    reported_object = GenericForeignKey(
        'reported_content_type',
        'reported_object_id'
    )
    
    # If reporting a user specifically (shortcut)
    reported_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_against',
        help_text='User being reported (if applicable)'
    )
    
    # Report details
    reason = models.CharField(
        max_length=50,
        choices=ReportReason.choices,
        help_text='Primary reason for the report'
    )
    description = models.TextField(
        blank=True,
        help_text='Additional details about the report'
    )
    evidence_image = models.ImageField(
        upload_to='reports/evidence/',
        null=True,
        blank=True,
        help_text='Screenshot or photo evidence'
    )
    evidence_file = models.FileField(
        upload_to='reports/evidence/',
        null=True,
        blank=True,
        help_text='Additional evidence file'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING,
        db_index=True,
        help_text='Current status of the report'
    )
    priority = models.PositiveSmallIntegerField(
        default=1,
        help_text='Priority level (1-5, higher = more urgent)'
    )
    
    # Moderation
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_reviewed',
        help_text='Admin who reviewed this report'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the report was reviewed'
    )
    action_taken = models.CharField(
        max_length=30,
        choices=ModeratorAction.choices,
        blank=True,
        help_text='Action taken by moderator'
    )
    action_notes = models.TextField(
        blank=True,
        help_text='Notes about the action taken'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the report was filed'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    class Meta:
        db_table = 'reports'
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['reported_content_type', 'reported_object_id']),
            models.Index(fields=['reporter', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reason']),
            models.Index(fields=['reported_user']),
        ]
    
    def __str__(self):
        return f'Report by {self.reporter.email} - {self.reason}'
    
    def clean(self):
        """Validate the report."""
        from django.core.exceptions import ValidationError
        super().clean()
        
        # Prevent self-reporting (for user reports)
        if self.reported_user and self.reported_user == self.reporter:
            raise ValidationError('Users cannot report themselves.')
    
    def start_review(self, reviewer, save=True):
        """Mark report as under review."""
        self.status = ReportStatus.UNDER_REVIEW
        self.reviewed_by = reviewer
        if save:
            self.save(update_fields=['status', 'reviewed_by', 'updated_at'])
    
    def take_action(self, reviewer, action, notes='', save=True):
        """
        Record the action taken on this report.
        """
        self.status = ReportStatus.ACTION_TAKEN
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.action_taken = action
        self.action_notes = notes
        
        if save:
            self.save(update_fields=[
                'status', 'reviewed_by', 'reviewed_at',
                'action_taken', 'action_notes', 'updated_at'
            ])
    
    def dismiss(self, reviewer, notes='', save=True):
        """Dismiss the report as not actionable."""
        self.status = ReportStatus.DISMISSED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.action_taken = ModeratorAction.NO_ACTION
        self.action_notes = notes
        
        if save:
            self.save(update_fields=[
                'status', 'reviewed_by', 'reviewed_at',
                'action_taken', 'action_notes', 'updated_at'
            ])
    
    def escalate(self, reviewer, notes='', save=True):
        """Escalate the report to higher admin."""
        self.status = ReportStatus.ESCALATED
        self.reviewed_by = reviewer
        self.action_taken = ModeratorAction.ESCALATED
        self.action_notes = notes
        self.priority = min(5, self.priority + 1)
        
        if save:
            self.save(update_fields=[
                'status', 'reviewed_by', 'action_taken',
                'action_notes', 'priority', 'updated_at'
            ])


class ReportAggregate(models.Model):
    """
    Cached aggregate of reports for an entity.
    Helps admins quickly see which entities have multiple reports.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Reported entity
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='report_aggregates'
    )
    object_id = models.CharField(
        max_length=255,
        help_text='ID of the reported object'
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Aggregate data
    total_reports = models.PositiveIntegerField(default=0)
    pending_reports = models.PositiveIntegerField(default=0)
    actioned_reports = models.PositiveIntegerField(default=0)
    
    # Last report info
    last_reported_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'report_aggregates'
        verbose_name = 'Report Aggregate'
        verbose_name_plural = 'Report Aggregates'
        unique_together = [['content_type', 'object_id']]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['total_reports']),
            models.Index(fields=['pending_reports']),
        ]
    
    def __str__(self):
        return f'{self.content_type.model}: {self.object_id} - {self.total_reports} reports'
    
    @classmethod
    def update_for_object(cls, content_type, object_id):
        """Update aggregate statistics for a specific object."""
        from django.db.models import Count, Max, Q
        
        reports = Report.objects.filter(
            reported_content_type=content_type,
            reported_object_id=str(object_id)
        )
        
        stats = reports.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status=ReportStatus.PENDING)),
            actioned=Count('id', filter=Q(status=ReportStatus.ACTION_TAKEN)),
            last_report=Max('created_at'),
        )
        
        if stats['total'] > 0:
            aggregate, _ = cls.objects.update_or_create(
                content_type=content_type,
                object_id=str(object_id),
                defaults={
                    'total_reports': stats['total'] or 0,
                    'pending_reports': stats['pending'] or 0,
                    'actioned_reports': stats['actioned'] or 0,
                    'last_reported_at': stats['last_report'],
                }
            )
            return aggregate
        return None


class UserBan(models.Model):
    """
    Track user bans resulting from reports.
    Supports temporary and permanent bans.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bans',
        help_text='Banned user'
    )
    
    # Related report (optional)
    related_report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resulting_bans',
        help_text='Report that led to this ban'
    )
    
    # Ban details
    reason = models.TextField(
        help_text='Reason for the ban'
    )
    is_permanent = models.BooleanField(
        default=False,
        help_text='Whether this is a permanent ban'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the ban expires (null for permanent)'
    )
    
    # Who issued the ban
    banned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bans_issued',
        help_text='Admin who issued the ban'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether the ban is currently active'
    )
    lifted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the ban was lifted'
    )
    lifted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bans_lifted',
        help_text='Admin who lifted the ban'
    )
    lift_reason = models.TextField(
        blank=True,
        help_text='Reason for lifting the ban'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the ban was issued'
    )
    
    class Meta:
        db_table = 'user_bans'
        verbose_name = 'User Ban'
        verbose_name_plural = 'User Bans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        status = 'permanent' if self.is_permanent else f'until {self.expires_at}'
        return f'Ban on {self.user.email} ({status})'
    
    def lift(self, lifted_by, reason='', save=True):
        """Lift the ban."""
        self.is_active = False
        self.lifted_at = timezone.now()
        self.lifted_by = lifted_by
        self.lift_reason = reason
        
        if save:
            self.save(update_fields=[
                'is_active', 'lifted_at', 'lifted_by', 'lift_reason'
            ])
    
    @property
    def is_expired(self):
        """Check if the ban has expired."""
        if self.is_permanent:
            return False
        if not self.expires_at:
            return True
        return timezone.now() >= self.expires_at


def create_report(reporter, reported_object, reason, description='', reported_user=None):
    """
    Utility function to create a report with proper content type handling.
    
    Usage:
        report = create_report(
            reporter=patient_user,
            reported_object=nurse_provider,
            reason=ReportReason.UNPROFESSIONAL,
            description="The nurse was rude.",
            reported_user=nurse_user  # Optional: the user behind the object
        )
    """
    reported_content_type = ContentType.objects.get_for_model(reported_object)
    
    report = Report.objects.create(
        reporter=reporter,
        reported_content_type=reported_content_type,
        reported_object_id=str(reported_object.pk),
        reported_user=reported_user,
        reason=reason,
        description=description
    )
    
    return report
