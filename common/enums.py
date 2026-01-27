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
