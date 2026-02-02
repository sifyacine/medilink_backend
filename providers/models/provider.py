"""
Base Provider model for all healthcare provider types.
"""
from django.db import models
from django.utils import timezone

from accounts.models import User
from common.enums import ProviderStatus, ProviderType


class Provider(models.Model):
    """
    Base provider model.
    One-to-one relationship with User.
    Tracks verification status and metadata.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='provider_profile',
        help_text='User account associated with this provider'
    )
    provider_type = models.CharField(
        max_length=20,
        choices=ProviderType.choices,
        help_text='Type of healthcare provider'
    )
    status = models.CharField(
        max_length=20,
        choices=ProviderStatus.choices,
        default=ProviderStatus.PENDING,
        db_index=True,
        help_text='Verification status'
    )
    refusal_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason for refusal (if status is REFUSED)'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the provider was approved'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_providers',
        help_text='Admin who approved this provider'
    )
    # Legacy fields for backward compatibility
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Legacy: When the provider was verified (use approved_at)'
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_providers',
        help_text='Legacy: Admin who verified this provider (use approved_by)'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='Provider profile creation timestamp'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    # Daily appointment limit (0 = unlimited)
    daily_appointment_limit = models.PositiveIntegerField(
        default=0,
        help_text='Maximum appointments per day (0 = unlimited)'
    )
    
    class Meta:
        db_table = 'providers'
        verbose_name = 'Provider'
        verbose_name_plural = 'Providers'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['provider_type']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f'{self.user.email} ({self.provider_type})'
    
    @property
    def is_approved(self):
        """Check if provider is approved."""
        return self.status == ProviderStatus.APPROVED
    
    @property
    def is_verified(self):
        """Legacy property - use is_approved instead."""
        return self.is_approved
    
    @property
    def is_pending(self):
        """Check if provider is pending verification."""
        return self.status == ProviderStatus.PENDING
    
    @property
    def is_refused(self):
        """Check if provider was refused."""
        return self.status == ProviderStatus.REFUSED
    
    def approve(self, approved_by):
        """Mark provider as approved."""
        self.status = ProviderStatus.APPROVED
        self.approved_at = timezone.now()
        self.approved_by = approved_by
        self.refusal_reason = None
        # Legacy fields
        self.verified_at = timezone.now()
        self.verified_by = approved_by
        self.save()
    
    def verify(self, verified_by):
        """Legacy method - use approve() instead."""
        self.approve(verified_by)
    
    def refuse(self, reason, refused_by):
        """Mark provider as refused with a reason."""
        if not reason or not reason.strip():
            raise ValueError('Refusal reason is required')
        self.status = ProviderStatus.REFUSED
        self.refusal_reason = reason.strip()
        self.verified_at = None
        self.verified_by = refused_by
        self.save()


# Note: Doctor, Nurse, Clinic, Laboratory, VTC, and Seller models
# are now in separate files:
# - providers/models/doctor.py
# - providers/models/nurse.py
# - providers/models/clinic.py
# - providers/models/laboratory.py
# - providers/models/vtc.py
# - providers/models/seller.py
