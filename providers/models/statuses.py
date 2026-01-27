"""
Provider status model for tracking verification workflow.
"""
from django.db import models
from django.utils import timezone

from accounts.models import User
from common.enums import ProviderStatus


class ProviderStatusHistory(models.Model):
    """
    Audit trail for provider status changes.
    Tracks who changed the status, when, and why.
    """
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        related_name='status_history',
        help_text='Provider whose status changed'
    )
    old_status = models.CharField(
        max_length=20,
        choices=ProviderStatus.choices,
        null=True,
        blank=True,
        help_text='Previous status'
    )
    new_status = models.CharField(
        max_length=20,
        choices=ProviderStatus.choices,
        help_text='New status'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='provider_status_changes',
        help_text='Admin who made the change'
    )
    reason = models.TextField(
        blank=True,
        help_text='Reason for status change (required for REFUSED)'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the status change occurred'
    )
    
    class Meta:
        db_table = 'provider_status_history'
        verbose_name = 'Provider Status History'
        verbose_name_plural = 'Provider Status Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', '-created_at']),
            models.Index(fields=['new_status']),
        ]
    
    def __str__(self):
        return f'{self.provider.user.email}: {self.old_status} -> {self.new_status}'
