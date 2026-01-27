"""
Medical Records models for patient-centered healthcare records.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from accounts.models import User
from providers.models import Provider


class MedicalRecord(models.Model):
    """
    Medical record model - owned by patient, accessible by authorized providers.
    
    Security:
    - Patients can view and add notes to their own records
    - Providers can only access records they are authorized to view
    - Full audit trail of who created/updated what
    """
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medical_records',
        help_text='Patient who owns this record'
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_records',
        help_text='Provider who created this record (if applicable)'
    )
    
    # Record Information
    title = models.CharField(
        max_length=200,
        help_text='Record title/summary'
    )
    record_type = models.CharField(
        max_length=50,
        choices=[
            ('CONSULTATION', 'Consultation'),
            ('DIAGNOSIS', 'Diagnosis'),
            ('PRESCRIPTION', 'Prescription'),
            ('LAB_RESULT', 'Lab Result'),
            ('IMAGING', 'Imaging'),
            ('SURGERY', 'Surgery'),
            ('HOSPITALIZATION', 'Hospitalization'),
            ('VACCINATION', 'Vaccination'),
            ('OTHER', 'Other'),
        ],
        default='CONSULTATION',
        help_text='Type of medical record'
    )
    
    # Medical Information
    diagnosis = models.TextField(
        blank=True,
        help_text='Diagnosis information'
    )
    symptoms = models.TextField(
        blank=True,
        help_text='Symptoms description'
    )
    treatment = models.TextField(
        blank=True,
        help_text='Treatment plan and procedures'
    )
    notes = models.TextField(
        blank=True,
        help_text='General notes'
    )
    
    # Dates
    record_date = models.DateTimeField(
        default=timezone.now,
        help_text='Date when the medical event occurred'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether record is active'
    )
    is_confidential = models.BooleanField(
        default=False,
        help_text='Whether record is marked as confidential'
    )
    
    # Audit Fields
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When record was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_medical_records',
        help_text='User who created this record'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_medical_records',
        help_text='User who last updated this record'
    )
    
    class Meta:
        db_table = 'medical_records'
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
        ordering = ['-record_date', '-created_at']
        indexes = [
            models.Index(fields=['patient', '-record_date']),
            models.Index(fields=['provider']),
            models.Index(fields=['record_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f'{self.title} - {self.patient.email}'


class Prescription(models.Model):
    """
    Prescription model linked to medical records.
    """
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        help_text='Medical record this prescription belongs to'
    )
    medication_name = models.CharField(
        max_length=200,
        help_text='Name of medication'
    )
    dosage = models.CharField(
        max_length=100,
        blank=True,
        help_text='Dosage information'
    )
    frequency = models.CharField(
        max_length=100,
        blank=True,
        help_text='Frequency of administration'
    )
    duration = models.CharField(
        max_length=100,
        blank=True,
        help_text='Duration of treatment'
    )
    instructions = models.TextField(
        blank=True,
        help_text='Special instructions'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether prescription is currently active'
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    
    class Meta:
        db_table = 'prescriptions'
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.medication_name} - {self.medical_record.title}'


class Allergy(models.Model):
    """
    Allergy model - patient allergies linked to medical records.
    """
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='allergies',
        help_text='Patient who has this allergy'
    )
    allergen = models.CharField(
        max_length=200,
        help_text='Allergen name (e.g., Penicillin, Peanuts)'
    )
    severity = models.CharField(
        max_length=50,
        choices=[
            ('MILD', 'Mild'),
            ('MODERATE', 'Moderate'),
            ('SEVERE', 'Severe'),
            ('LIFE_THREATENING', 'Life Threatening'),
        ],
        default='MODERATE',
        help_text='Allergy severity'
    )
    reaction = models.TextField(
        blank=True,
        help_text='Reaction description'
    )
    diagnosed_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date allergy was diagnosed'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether allergy is currently active'
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'allergies'
        verbose_name = 'Allergy'
        verbose_name_plural = 'Allergies'
        indexes = [
            models.Index(fields=['patient', 'is_active']),
        ]
    
    def __str__(self):
        return f'{self.patient.email} - {self.allergen}'


class MedicalRecordAttachment(models.Model):
    """
    Attachments for medical records (labs, scans, PDFs, images).
    """
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text='Medical record this attachment belongs to'
    )
    file = models.FileField(
        upload_to='medical_records/attachments/',
        help_text='Attachment file (PDF, image, etc.)'
    )
    file_type = models.CharField(
        max_length=50,
        choices=[
            ('PDF', 'PDF Document'),
            ('IMAGE', 'Image'),
            ('LAB_RESULT', 'Lab Result'),
            ('SCAN', 'Scan/Imaging'),
            ('OTHER', 'Other'),
        ],
        default='OTHER',
        help_text='Type of attachment'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text='Attachment description'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments',
        help_text='User who uploaded this attachment'
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    
    class Meta:
        db_table = 'medical_record_attachments'
        verbose_name = 'Medical Record Attachment'
        verbose_name_plural = 'Medical Record Attachments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.medical_record.title} - {self.description or self.file.name}'


class MedicalRecordNote(models.Model):
    """
    Notes on medical records - can be from patient or provider.
    """
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='record_notes',
        help_text='Medical record this note belongs to'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medical_notes',
        help_text='User who wrote this note'
    )
    note_type = models.CharField(
        max_length=50,
        choices=[
            ('PATIENT', 'Patient Note'),
            ('PROVIDER', 'Provider Note'),
            ('SYSTEM', 'System Note'),
        ],
        help_text='Type of note'
    )
    content = models.TextField(
        help_text='Note content'
    )
    is_visible_to_patient = models.BooleanField(
        default=True,
        help_text='Whether note is visible to patient'
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'medical_record_notes'
        verbose_name = 'Medical Record Note'
        verbose_name_plural = 'Medical Record Notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medical_record', '-created_at']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f'Note on {self.medical_record.title} by {self.author.email}'


class ProviderAccess(models.Model):
    """
    Tracks which providers have access to which patient's medical records.
    This enforces authorization - providers can only access records they're authorized for.
    """
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authorized_providers',
        help_text='Patient whose records are being accessed'
    )
    provider = models.ForeignKey(
        Provider,
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
        choices=[
            ('FULL', 'Full Access'),
            ('READ_ONLY', 'Read Only'),
            ('LIMITED', 'Limited Access'),
        ],
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
        help_text='Whether access is currently active'
    )
    notes = models.TextField(
        blank=True,
        help_text='Notes about this access grant'
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
