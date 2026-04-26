"""
Comprehensive Clinic model for healthcare marketplace.
"""
from django.db import models
from django.utils import timezone

from providers.models.provider import Provider


class Clinic(models.Model):
    """
    Comprehensive Clinic profile model.
    Extends base Provider with detailed clinic information.
    """
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='clinic_profile',
        help_text='Base provider profile'
    )
    
    # Clinic Information
    clinic_name = models.CharField(
        max_length=200,
        db_index=True,
        blank=True,
        help_text='Name of the clinic'
    )
    license_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
        help_text='Clinic license number (unique)'
    )
    
    # Visual identity
    logo = models.ImageField(
        upload_to='clinics/logos/',
        null=True,
        blank=True,
        help_text='Clinic logo or profile image'
    )
    
    # Contact Information
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Primary phone number'
    )
    email = models.EmailField(
        blank=True,
        help_text='Clinic email (can be different from user email)'
    )
    website = models.URLField(
        blank=True,
        help_text='Clinic website URL'
    )
    
    # Description
    description = models.TextField(
        blank=True,
        help_text='Clinic description and services offered'
    )
    
    # Facilities & capabilities
    number_of_beds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Number of beds available in the clinic'
    )
    has_emergency_services = models.BooleanField(
        default=False,
        help_text='Whether the clinic provides emergency services'
    )
    is_24_hours = models.BooleanField(
        default=False,
        help_text='Whether the clinic operates 24/7'
    )
    outpatient_capacity_per_day = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Approximate number of outpatients that can be seen per day'
    )
    
    # Verification Documents
    license_document = models.FileField(
        upload_to='clinics/documents/licenses/',
        null=True,
        blank=True,
        help_text='Clinic license document (PDF or image)'
    )
    
    # Status & Verification Flags
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether clinic documents are verified'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether clinic is currently available'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='Profile creation timestamp'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    class Meta:
        db_table = 'clinics'
        verbose_name = 'Clinic'
        verbose_name_plural = 'Clinics'
        indexes = [
            models.Index(fields=['clinic_name']),
            models.Index(fields=['license_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_available']),
            models.Index(fields=['has_emergency_services']),
            models.Index(fields=['is_24_hours']),
        ]
    
    def __str__(self):
        return self.clinic_name
