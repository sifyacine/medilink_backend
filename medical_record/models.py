"""
Medical Records models for patient-centered healthcare data management.

Supports two patient linking strategies:
1. patient (User) - For patients with Medilink accounts
2. patient_record (PatientRecord) - For patients without accounts

At least one must be set. If both are set, they should be consistent
(patient_record.linked_user == patient).
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from accounts.models import User
from common.enums import UserRole


class MedicalRecord(models.Model):
    """
    Main medical record model.
    Owned by a patient, accessible by authorized providers.
    
    Supports both:
    - Patients with accounts (via patient FK)
    - Patients without accounts (via patient_record FK)
    
    At least one of patient or patient_record must be set.
    """
    # Link to User (for patients with accounts)
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='medical_records',
        limit_choices_to={'role': UserRole.PATIENT},
        help_text='Patient who owns this medical record (if they have an account)'
    )
    
    # Link to PatientRecord (for patients without accounts)
    patient_record = models.ForeignKey(
        'patients.PatientRecord',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='medical_records',
        help_text='Patient record (for patients without accounts)'
    )
    
    def clean(self):
        """Validate that at least one patient link is set."""
        super().clean()
        if not self.patient and not self.patient_record:
            raise ValidationError(
                'A medical record must be linked to either a patient user or a patient record.'
            )
        # If both are set, validate consistency
        if self.patient and self.patient_record:
            if self.patient_record.linked_user and self.patient_record.linked_user != self.patient:
                raise ValidationError(
                    'Patient record is linked to a different user than the specified patient.'
                )
    
    def save(self, *args, **kwargs):
        """Ensure validation runs on save."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def patient_display_name(self):
        """Get the patient's display name using centralized utility."""
        from common.utils import get_patient_display_name
        return get_patient_display_name(self.patient, self.patient_record)
    
    @property
    def effective_patient_id(self):
        """Get the effective patient identifier."""
        if self.patient_record:
            return self.patient_record.patient_unique_id
        if self.patient:
            return f"USER-{self.patient.id}"
        return None
    
    # Record metadata
    title = models.CharField(
        max_length=200,
        help_text='Title or summary of the medical record'
    )
    record_type = models.CharField(
        max_length=50,
        choices=[
            ('DIAGNOSIS', 'Diagnosis'),
            ('PRESCRIPTION', 'Prescription'),
            ('ALLERGY', 'Allergy'),
            ('LAB_RESULT', 'Lab Result'),
            ('IMAGING', 'Imaging Study'),
            ('PROCEDURE', 'Procedure'),
            ('NOTE', 'General Note'),
            ('VACCINATION', 'Vaccination'),
            ('OTHER', 'Other'),
        ],
        default='NOTE',
        db_index=True,
        help_text='Type of medical record'
    )
    
    # Clinical information
    diagnosis_code = models.CharField(
        max_length=50,
        blank=True,
        help_text='ICD-10 or other diagnosis code'
    )
    description = models.TextField(
        help_text='Detailed description of the medical record'
    )
    symptoms = models.TextField(
        blank=True,
        help_text='Symptoms reported or observed'
    )
    
    # Dates
    record_date = models.DateField(
        help_text='Date when the medical event occurred'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When this record was created in the system'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    # Provider information
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_medical_records',
        limit_choices_to={'role': UserRole.PROVIDER},
        help_text='Provider who created this record'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_medical_records',
        help_text='User who last updated this record'
    )
    
    # Status and flags
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether this record is active (not archived)'
    )
    is_confidential = models.BooleanField(
        default=False,
        help_text='Whether this record is marked as confidential'
    )
    requires_followup = models.BooleanField(
        default=False,
        help_text='Whether this record requires follow-up'
    )
    followup_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date for follow-up appointment or check'
    )

    # Organization and severity
    sequence_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Sequential number for ordering this patient\'s records'
    )
    folder_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Custom folder/category name for organization (e.g., "Cardiology", "Surgery")'
    )
    severity_level = models.CharField(
        max_length=20,
        choices=[
            ('CRITICAL', 'Critical'),
            ('HIGH', 'High'),
            ('MEDIUM', 'Medium'),
            ('LOW', 'Low'),
            ('INFO', 'Informational'),
        ],
        default='MEDIUM',
        db_index=True,
        help_text='Clinical severity level of this medical event'
    )
    timeline_order = models.IntegerField(
        default=0,
        db_index=True,
        help_text='Numeric value for ordering records in timeline view'
    )
    
    class Meta:
        db_table = 'medical_records'
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
        ordering = ['-record_date', '-created_at']
        indexes = [
            models.Index(fields=['patient', '-record_date']),
            models.Index(fields=['patient_record', '-record_date']),
            models.Index(fields=['record_type']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active', '-record_date']),
            models.Index(fields=['requires_followup', 'followup_date']),
            models.Index(fields=['severity_level', '-record_date']),
            models.Index(fields=['patient', 'folder_name']),
            models.Index(fields=['patient', 'severity_level', '-record_date']),
        ]
    
    def __str__(self):
        return f'{self.title} - {self.patient_display_name} ({self.record_date})'


class Prescription(models.Model):
    """
    Prescription information linked to a medical record.
    """
    medical_record = models.OneToOneField(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescription',
        help_text='Medical record this prescription belongs to'
    )
    
    medication_name = models.CharField(
        max_length=200,
        help_text='Name of the medication'
    )
    dosage = models.CharField(
        max_length=100,
        help_text='Dosage information (e.g., "500mg", "2 tablets")'
    )
    frequency = models.CharField(
        max_length=100,
        help_text='Frequency of administration (e.g., "twice daily", "as needed")'
    )
    duration = models.CharField(
        max_length=100,
        blank=True,
        help_text='Duration of treatment (e.g., "7 days", "until finished")'
    )
    instructions = models.TextField(
        blank=True,
        help_text='Additional instructions for taking the medication'
    )
    quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Quantity prescribed'
    )
    refills = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(12)],
        help_text='Number of refills allowed'
    )
    
    class Meta:
        db_table = 'prescriptions'
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'
    
    def __str__(self):
        return f'{self.medication_name} - {self.medical_record.patient_display_name}'


class Allergy(models.Model):
    """
    Allergy information linked to a medical record.
    """
    medical_record = models.OneToOneField(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='allergy',
        help_text='Medical record this allergy belongs to'
    )
    
    allergen = models.CharField(
        max_length=200,
        help_text='Substance causing the allergy'
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('MILD', 'Mild'),
            ('MODERATE', 'Moderate'),
            ('SEVERE', 'Severe'),
            ('LIFE_THREATENING', 'Life-threatening'),
        ],
        default='MODERATE',
        help_text='Severity of the allergic reaction'
    )
    reaction = models.TextField(
        help_text='Description of the allergic reaction'
    )
    first_observed = models.DateField(
        null=True,
        blank=True,
        help_text='Date when allergy was first observed'
    )
    
    class Meta:
        db_table = 'allergies'
        verbose_name = 'Allergy'
        verbose_name_plural = 'Allergies'
    
    def __str__(self):
        return f'{self.allergen} allergy - {self.medical_record.patient_display_name}'


class MedicalRecordAttachment(models.Model):
    """
    File attachments for medical records (lab results, scans, PDFs, images).
    """
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text='Medical record this attachment belongs to'
    )
    
    file = models.FileField(
        upload_to='medical_records/attachments/%Y/%m/%d/',
        help_text='Attachment file (PDF, image, etc.)'
    )
    file_name = models.CharField(
        max_length=255,
        help_text='Original file name'
    )
    file_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='File type/MIME type'
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='File size in bytes'
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        help_text='Description of the attachment'
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_attachments',
        help_text='User who uploaded this attachment'
    )
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        help_text='When attachment was uploaded'
    )
    
    class Meta:
        db_table = 'medical_record_attachments'
        verbose_name = 'Medical Record Attachment'
        verbose_name_plural = 'Medical Record Attachments'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f'{self.file_name} - {self.medical_record.title}'


class MedicalRecordNote(models.Model):
    """
    Notes associated with medical records.
    Can be patient notes or provider notes.
    """
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='notes',
        help_text='Medical record this note belongs to'
    )
    
    note_type = models.CharField(
        max_length=20,
        choices=[
            ('PATIENT', 'Patient Note'),
            ('PROVIDER', 'Provider Note'),
            ('SYSTEM', 'System Note'),
        ],
        default='PROVIDER',
        db_index=True,
        help_text='Type of note'
    )
    content = models.TextField(
        help_text='Note content'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_record_notes',
        help_text='User who created this note'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When note was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    # Provider notes can be locked to prevent patient modification
    is_locked = models.BooleanField(
        default=False,
        help_text='Whether this note is locked (provider notes are typically locked)'
    )
    
    class Meta:
        db_table = 'medical_record_notes'
        verbose_name = 'Medical Record Note'
        verbose_name_plural = 'Medical Record Notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medical_record', '-created_at']),
            models.Index(fields=['note_type']),
        ]
    
    def __str__(self):
        return f'{self.note_type} note - {self.medical_record.title}'


class MedicalRecordAccessLog(models.Model):
    """
    Audit trail for medical record access.
    Tracks who accessed which records and when.
    """
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='access_logs',
        help_text='Medical record that was accessed'
    )
    
    accessed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_record_accesses',
        help_text='User who accessed the record'
    )
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('VIEW', 'View'),
            ('CREATE', 'Create'),
            ('UPDATE', 'Update'),
            ('DELETE', 'Delete'),
            ('PDF_EXPORT', 'PDF Export'),
        ],
        help_text='Type of access'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the access'
    )
    accessed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When access occurred'
    )
    
    class Meta:
        db_table = 'medical_record_access_logs'
        verbose_name = 'Medical Record Access Log'
        verbose_name_plural = 'Medical Record Access Logs'
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['medical_record', '-accessed_at']),
            models.Index(fields=['accessed_by', '-accessed_at']),
            models.Index(fields=['access_type']),
        ]
    
    def __str__(self):
        return f'{self.access_type} by {self.accessed_by.email if self.accessed_by else "Unknown"} - {self.accessed_at}'


class ProviderAccess(models.Model):
    """
    Tracks which providers have access to which patient's medical records.
    This enforces authorization - providers can only access records they're authorized for.
    """
    ACCESS_TYPES = [
        ('FULL', 'Full Access'),
        ('READ_ONLY', 'Read Only'),
        ('LIMITED', 'Limited Access'),
    ]
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authorized_providers',
        limit_choices_to={'role': UserRole.PATIENT},
        help_text='Patient whose records are being accessed'
    )
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        related_name='authorized_patients',
        help_text='Provider who has access'
    )
    access_granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_accesses',
        help_text='User who granted this access (patient or admin)'
    )
    access_type = models.CharField(
        max_length=50,
        choices=ACCESS_TYPES,
        default='READ_ONLY',
        help_text='Type of access granted'
    )
    granted_at = models.DateTimeField(
        default=timezone.now,
        help_text='When access was granted'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When access expires (null = permanent)'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether access is currently active'
    )
    reason = models.TextField(
        blank=True,
        help_text='Reason for granting access'
    )
    
    class Meta:
        db_table = 'provider_access'
        verbose_name = 'Provider Access'
        verbose_name_plural = 'Provider Accesses'
        unique_together = [['patient', 'provider']]
        indexes = [
            models.Index(fields=['patient', 'is_active']),
            models.Index(fields=['provider', 'is_active']),
        ]
    
    def __str__(self):
        return f'{self.provider.user.email} -> {self.patient.email} ({self.access_type})'
    
    @property
    def is_expired(self):
        """Check if access has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def is_valid(self):
        """Check if access is valid (active and not expired)."""
        return self.is_active and not self.is_expired
