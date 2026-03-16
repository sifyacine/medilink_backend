"""
AdminActivityLog model — immutable audit trail of every admin action.
"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from common.enums import AdminActionType


class AdminActivityLog(models.Model):
    """
    Immutable audit record created whenever an admin performs a write action.

    Every admin view that changes state is responsible for firing the
    ``admin_action_performed`` signal (defined in admins/signals.py) which
    creates one of these records automatically.

    Fields:
        admin        — The admin user who performed the action (SET_NULL so logs
                       survive if the admin account is deleted).
        action       — One of AdminActionType choices.
        content_type — ContentType of the target object (nullable for global actions).
        object_id    — PK of the target object.
        object_repr  — Human-readable snapshot of the target at log time.
        ip_address   — IP extracted from the request.
        extra_data   — Arbitrary JSON (e.g. old_status / new_status / reason).
        created_at   — Immutable timestamp.
    """
    admin = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_activity_logs',
        help_text='Admin who performed the action',
    )
    action = models.CharField(
        max_length=50,
        choices=AdminActionType.choices,
        db_index=True,
        help_text='Type of admin action',
    )
    # Generic FK — can point to User, Provider, PatientRecord, BlogPost, etc.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    object_repr = models.CharField(
        max_length=300,
        blank=True,
        help_text='String representation of the target object at log time',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the admin at time of action',
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context (old/new values, reason, etc.)',
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When this action occurred (immutable)',
    )

    class Meta:
        db_table = 'admin_activity_logs'
        verbose_name = 'Admin Activity Log'
        verbose_name_plural = 'Admin Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        admin_email = self.admin.email if self.admin else 'deleted-admin'
        return f'[{self.created_at:%Y-%m-%d %H:%M}] {admin_email} — {self.action}'
