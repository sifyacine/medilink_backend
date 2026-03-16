"""
AdminProfile model — sub-role assignment for ADMIN users.
"""
from django.db import models
from django.utils import timezone

from common.enums import AdminSubRole


class AdminProfile(models.Model):
    """
    Extended profile for ADMIN users.

    Each user with role == ADMIN should have exactly one AdminProfile
    that determines which sub-role features they can access.

    Sub-roles:
        SUPER_ADMIN    — Full platform access, can manage other admins.
        MODERATOR      — Approve/refuse providers, suspend users.
        SUPPORT        — Read-only access to users/logs, can send password resets.
        CONTENT_EDITOR — Manage platform content (landing page, blog, FAQs, etc.).
    """
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='admin_profile',
        help_text='The ADMIN user this profile belongs to',
    )
    sub_role = models.CharField(
        max_length=30,
        choices=AdminSubRole.choices,
        default=AdminSubRole.SUPPORT,
        db_index=True,
        help_text='Admin sub-role controlling feature access',
    )
    notes = models.TextField(
        blank=True,
        help_text='Internal notes about this admin (visible only to SUPER_ADMINs)',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'admin_profiles'
        verbose_name = 'Admin Profile'
        verbose_name_plural = 'Admin Profiles'

    def __str__(self):
        return f'{self.user.email} [{self.get_sub_role_display()}]'
