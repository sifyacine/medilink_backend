"""
Centralized enums for the Medilink platform.
All role and status strings should reference these enums, not hardcoded strings.
"""
from django.db import models


class UserRole(models.TextChoices):
    """User roles in the system."""
    PATIENT = 'PATIENT', 'Patient'
    PROVIDER = 'PROVIDER', 'Provider'
    ADMIN = 'ADMIN', 'Admin'


class ProviderStatus(models.TextChoices):
    """Provider account approval status."""
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REFUSED = 'REFUSED', 'Refused'
    SUSPENDED = 'SUSPENDED', 'Suspended'  # Provider suspended after approval


class ProviderType(models.TextChoices):
    """Types of healthcare providers."""
    DOCTOR = 'DOCTOR', 'Doctor'
    NURSE = 'NURSE', 'Nurse'
    CLINIC = 'CLINIC', 'Clinic'
    LABORATORY = 'LABORATORY', 'Laboratory'
    VTC = 'VTC', 'Healthcare VTC'
    SELLER = 'SELLER', 'Seller'


class UserAccountStatus(models.TextChoices):
    """
    User account status (separate from provider verification status).
    
    ACTIVE: Account is active and can be used normally
    SUSPENDED: Account temporarily disabled (e.g., policy violation)
    DEACTIVATED: Account permanently disabled by user or admin
    """
    ACTIVE = 'ACTIVE', 'Active'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    DEACTIVATED = 'DEACTIVATED', 'Deactivated'


class AdminSubRole(models.TextChoices):
    """
    Sub-roles within the ADMIN user role.
    
    SUPER_ADMIN:    Full access — can manage other admins, all platform features.
    MODERATOR:      Approve/refuse providers, suspend users, moderate reports.
    SUPPORT:        View users & logs, reset passwords (mostly read-only).
    CONTENT_EDITOR: Manage platform content only (landing page, FAQ, blog, etc.).
    """
    SUPER_ADMIN    = 'SUPER_ADMIN',    'Super Admin'
    MODERATOR      = 'MODERATOR',      'Moderator'
    SUPPORT        = 'SUPPORT',        'Support'
    CONTENT_EDITOR = 'CONTENT_EDITOR', 'Content Editor'


class AdminActionType(models.TextChoices):
    """Action types recorded in the AdminActivityLog."""
    USER_SUSPEND        = 'USER_SUSPEND',        'User Suspended'
    USER_ACTIVATE       = 'USER_ACTIVATE',       'User Activated'
    USER_DEACTIVATE     = 'USER_DEACTIVATE',     'User Deactivated'
    USER_PASSWORD_RESET = 'USER_PASSWORD_RESET', 'Password Reset Sent'
    PROVIDER_APPROVE    = 'PROVIDER_APPROVE',    'Provider Approved'
    PROVIDER_REFUSE     = 'PROVIDER_REFUSE',     'Provider Refused'
    PROVIDER_SUSPEND    = 'PROVIDER_SUSPEND',    'Provider Suspended'
    PROVIDER_RESTORE    = 'PROVIDER_RESTORE',    'Provider Restored'
    PATIENT_SUSPEND     = 'PATIENT_SUSPEND',     'Patient Suspended'
    CONTENT_CREATE      = 'CONTENT_CREATE',      'Content Created'
    CONTENT_UPDATE      = 'CONTENT_UPDATE',      'Content Updated'
    CONTENT_DELETE      = 'CONTENT_DELETE',      'Content Deleted'
