"""
Patient Record models for managing patient data without accounts.

This module provides the ability for any provider (doctor, nurse, clinic,
laboratory, VTC, etc.) to create patient records for patients who do not
have Medilink accounts yet.

Key features:
- Patient records store essential patient data without authentication credentials
- Each record has a unique patient_unique_id (short, user-friendly) for identification
- Each record has a secure linking token for future account linking
- Tokens are one-time use, unique, and non-guessable
- When a patient later creates an account, they can link their existing records
- Soft delete support for safe data management
"""
import secrets
import uuid
import hashlib
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from accounts.models import User
from providers.models.provider import Provider
from common.enums import UserRole


def generate_linking_token():
    """Generate a unique, secure, non-guessable linking token."""
    return secrets.token_urlsafe(32)  # 256-bit secure token


def generate_patient_unique_id():
    """
    Generate a short, user-friendly patient unique ID.
    Format: MED-XXXXXX (8 character alphanumeric after prefix)
    """
    random_part = secrets.token_hex(4).upper()  # 8 chars
    return f"MED-{random_part}"


class Gender(models.TextChoices):
    """Gender choices for patient records."""
    MALE = 'MALE', 'Male'
    FEMALE = 'FEMALE', 'Female'
    OTHER = 'OTHER', 'Other'
    PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY', 'Prefer not to say'


class BloodType(models.TextChoices):
    """Blood type choices."""
    A_POSITIVE = 'A+', 'A+'
    A_NEGATIVE = 'A-', 'A-'
    B_POSITIVE = 'B+', 'B+'
    B_NEGATIVE = 'B-', 'B-'
    AB_POSITIVE = 'AB+', 'AB+'
    AB_NEGATIVE = 'AB-', 'AB-'
    O_POSITIVE = 'O+', 'O+'
    O_NEGATIVE = 'O-', 'O-'
    UNKNOWN = 'UNKNOWN', 'Unknown'


class PatientRecord(models.Model):
    """
    Patient record for patients without Medilink accounts.
    
    This model stores patient information created by providers for patients
    who may not have the Medilink app or a user account yet.
    
    Key behaviors:
    - No authentication credentials stored
    - patient_unique_id: Short, user-friendly identifier (MED-XXXXXX)
    - linking_token: Secure token for future account linking
    - Can be linked to a User account when patient registers
    - Multiple providers can access the same patient record
    - Soft delete support for safe data management
    """
    
    # Unique patient identifier (short, user-friendly)
    patient_unique_id = models.CharField(
        max_length=20,
        unique=True,
        default=generate_patient_unique_id,
        db_index=True,
        help_text='Unique patient identifier (e.g., MED-A1B2C3D4)'
    )
    
    # Linking to User Account (NULL until patient creates account)
    linked_user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_record',
        limit_choices_to={'role': UserRole.PATIENT},
        help_text='Linked user account (if patient has registered)'
    )
    
    # Unique linking token for account linking
    linking_token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_linking_token,
        db_index=True,
        help_text='Unique, secure token for linking to a user account'
    )
    token_used = models.BooleanField(
        default=False,
        help_text='Whether the linking token has been used'
    )
    token_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the token was used'
    )
    
    # Personal Information
    first_name = models.CharField(
        max_length=100,
        help_text='Patient first name'
    )
    last_name = models.CharField(
        max_length=100,
        help_text='Patient last name'
    )
    date_of_birth = models.DateField(
        help_text='Patient date of birth'
    )
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        help_text='Patient gender'
    )
    
    # Contact Information
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Patient phone number'
    )
    email = models.EmailField(
        blank=True,
        help_text='Patient email (optional, not for login)'
    )
    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Emergency contact name'
    )
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Emergency contact phone'
    )
    
    # Medical Information
    blood_type = models.CharField(
        max_length=10,
        choices=BloodType.choices,
        default=BloodType.UNKNOWN,
        help_text='Patient blood type'
    )
    known_allergies = models.TextField(
        blank=True,
        help_text='Known allergies (free text)'
    )
    chronic_conditions = models.TextField(
        blank=True,
        help_text='Chronic conditions (free text)'
    )
    current_medications = models.TextField(
        blank=True,
        help_text='Current medications (free text)'
    )
    
    # National ID (optional, for identification)
    national_id = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text='National ID number (optional, for identification)'
    )
    
    # Address Information (basic)
    address = models.TextField(
        blank=True,
        help_text='Patient address'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text='City'
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        help_text='State/Province'
    )
    country = models.CharField(
        max_length=100,
        default='Algeria',
        help_text='Country'
    )
    
    # Record Metadata
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the patient'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether the patient record is active'
    )
    
    # Soft delete support
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether the record is soft deleted'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the record was soft deleted'
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_patient_records',
        help_text='User who deleted this record'
    )
    
    # Audit fields
    created_by_provider = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_patient_records',
        help_text='Provider who created this patient record'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When this record was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    class Meta:
        db_table = 'patient_records'
        verbose_name = 'Patient Record'
        verbose_name_plural = 'Patient Records'
        indexes = [
            models.Index(fields=['patient_unique_id']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['national_id']),
            models.Index(fields=['linking_token']),
            models.Index(fields=['linked_user']),
            models.Index(fields=['is_active', 'is_deleted']),
            models.Index(fields=['created_by_provider']),
        ]
    
    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.date_of_birth})'
    
    @property
    def full_name(self):
        """Return the patient's full name."""
        return f'{self.first_name} {self.last_name}'
    
    @property
    def is_linked(self):
        """Check if this record is linked to a user account."""
        return self.linked_user is not None
    
    @property
    def age(self):
        """Calculate patient's age."""
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def regenerate_token(self):
        """
        Regenerate the linking token.
        Use this if the token needs to be reissued (e.g., lost token).
        """
        self.linking_token = generate_linking_token()
        self.token_used = False
        self.token_used_at = None
        self.save(update_fields=['linking_token', 'token_used', 'token_used_at'])
        return self.linking_token
    
    def link_to_user(self, user):
        """
        Link this patient record to a user account.
        
        Args:
            user: The User instance to link to
            
        Returns:
            bool: True if linking was successful
            
        Raises:
            ValueError: If token already used, record already linked,
                       or user is not a patient
        """
        if self.token_used:
            raise ValueError('This linking token has already been used.')
        
        if self.linked_user is not None:
            raise ValueError('This patient record is already linked to an account.')
        
        if user.role != UserRole.PATIENT:
            raise ValueError('User must have PATIENT role to link patient records.')
        
        # Check if user already has a linked patient record
        if hasattr(user, 'patient_record') and user.patient_record is not None:
            raise ValueError('This user account is already linked to a patient record.')
        
        # Link the record
        self.linked_user = user
        self.token_used = True
        self.token_used_at = timezone.now()
        self.save(update_fields=['linked_user', 'token_used', 'token_used_at'])
        
        return True
    
    def soft_delete(self, deleted_by_user=None):
        """
        Soft delete the patient record.
        
        Args:
            deleted_by_user: The user who initiated the deletion
        """
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by_user
        self.save(update_fields=['is_deleted', 'is_active', 'deleted_at', 'deleted_by'])
    
    def restore(self):
        """Restore a soft-deleted patient record."""
        self.is_deleted = False
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'is_active', 'deleted_at', 'deleted_by'])


class ProviderPatientAccess(models.Model):
    """
    Tracks which providers have access to which patient records.
    
    This enables:
    - Providers can only access patients they are authorized to see
    - Multiple providers can access the same patient record
    - Audit trail of who has accessed patient data
    """
    
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='patient_access',
        help_text='Provider with access to the patient'
    )
    patient_record = models.ForeignKey(
        PatientRecord,
        on_delete=models.CASCADE,
        related_name='provider_access',
        help_text='Patient record the provider can access'
    )
    
    # Access level
    access_level = models.CharField(
        max_length=20,
        choices=[
            ('FULL', 'Full Access'),
            ('READ_ONLY', 'Read Only'),
            ('LIMITED', 'Limited Access'),
        ],
        default='FULL',
        help_text='Level of access the provider has'
    )
    
    # Access granted by
    granted_by = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_access',
        help_text='Provider who granted this access'
    )
    
    # Audit fields
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When access was granted'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    class Meta:
        db_table = 'provider_patient_access'
        verbose_name = 'Provider Patient Access'
        verbose_name_plural = 'Provider Patient Access'
        unique_together = [['provider', 'patient_record']]
        indexes = [
            models.Index(fields=['provider']),
            models.Index(fields=['patient_record']),
        ]
    
    def __str__(self):
        return f'{self.provider} -> {self.patient_record} ({self.access_level})'


def generate_share_token():
    """Generate a secure, unique share token for medical record sharing."""
    return secrets.token_urlsafe(24)  # 192-bit secure token


class MedicalRecordShareToken(models.Model):
    """
    Time-limited, secure token for sharing medical records.
    
    Enables patients to share their medical records with new providers
    via QR code or token link without permanently granting access.
    
    Features:
    - Time-limited access (configurable expiry)
    - Single or multi-use tokens
    - Access logging
    - Revocable at any time
    """
    
    # Token identification
    token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_share_token,
        db_index=True,
        help_text='Unique share token'
    )
    
    # Patient who created the share
    patient_record = models.ForeignKey(
        PatientRecord,
        on_delete=models.CASCADE,
        related_name='share_tokens',
        help_text='Patient record being shared'
    )
    
    # Optionally link to patient user (if they have an account)
    created_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_share_tokens',
        help_text='User who created this share token'
    )
    
    # Access configuration
    access_level = models.CharField(
        max_length=20,
        choices=[
            ('READ_ONLY', 'Read Only'),
            ('FULL', 'Full Access'),
            ('LIMITED', 'Limited Access'),
        ],
        default='READ_ONLY',
        help_text='Level of access granted by this token'
    )
    
    # Time limits
    expires_at = models.DateTimeField(
        help_text='When this share token expires'
    )
    
    # Usage limits
    max_uses = models.PositiveIntegerField(
        default=1,
        help_text='Maximum number of times this token can be used (0 = unlimited)'
    )
    use_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of times this token has been used'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether this token is active'
    )
    is_revoked = models.BooleanField(
        default=False,
        help_text='Whether this token has been revoked'
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the token was revoked'
    )
    
    # Audit fields
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When this token was created'
    )
    
    # Optional: Restrict to specific provider (for targeted sharing)
    target_provider = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='targeted_share_tokens',
        help_text='Specific provider this token is for (null = any provider)'
    )
    
    # Optional notes about the share
    notes = models.TextField(
        blank=True,
        help_text='Optional notes about this share'
    )
    
    class Meta:
        db_table = 'medical_record_share_tokens'
        verbose_name = 'Medical Record Share Token'
        verbose_name_plural = 'Medical Record Share Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['patient_record', 'is_active']),
            models.Index(fields=['expires_at', 'is_active']),
        ]
    
    def __str__(self):
        return f'Share token for {self.patient_record} (expires: {self.expires_at})'
    
    @property
    def is_expired(self):
        """Check if the token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_usable(self):
        """Check if the token can still be used."""
        if not self.is_active or self.is_revoked:
            return False
        if self.is_expired:
            return False
        if self.max_uses > 0 and self.use_count >= self.max_uses:
            return False
        return True
    
    def record_use(self, provider=None):
        """
        Record that this token was used.
        
        Args:
            provider: The provider who used the token
            
        Returns:
            bool: True if use was recorded successfully
        """
        if not self.is_usable:
            return False
        
        self.use_count += 1
        self.save(update_fields=['use_count'])
        
        # Log the access
        ShareTokenAccessLog.objects.create(
            share_token=self,
            accessed_by_provider=provider,
        )
        
        return True
    
    def revoke(self):
        """Revoke this share token."""
        self.is_revoked = True
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=['is_revoked', 'is_active', 'revoked_at'])


class ShareTokenAccessLog(models.Model):
    """
    Log of accesses using share tokens.
    Provides audit trail for medical record sharing.
    """
    share_token = models.ForeignKey(
        MedicalRecordShareToken,
        on_delete=models.CASCADE,
        related_name='access_logs',
        help_text='Share token that was used'
    )
    accessed_by_provider = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='share_token_accesses',
        help_text='Provider who used this token'
    )
    accessed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When access occurred'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the access'
    )
    
    class Meta:
        db_table = 'share_token_access_logs'
        verbose_name = 'Share Token Access Log'
        verbose_name_plural = 'Share Token Access Logs'
        ordering = ['-accessed_at']
    
    def __str__(self):
        provider_name = self.accessed_by_provider.user.email if self.accessed_by_provider else 'Unknown'
        return f'Access by {provider_name} at {self.accessed_at}'