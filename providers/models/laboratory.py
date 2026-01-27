"""
Comprehensive Laboratory model for healthcare marketplace.
"""
from django.db import models
from django.utils import timezone

from providers.models.provider import Provider


class Laboratory(models.Model):
    """
    Comprehensive Laboratory profile model.
    Extends base Provider with detailed laboratory information.
    """
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='laboratory_profile',
        help_text='Base provider profile'
    )
    
    # Laboratory Information
    lab_name = models.CharField(
        max_length=200,
        db_index=True,
        blank=True,
        help_text='Name of the laboratory'
    )
    license_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        blank=True,
        help_text='Laboratory license number (unique)'
    )
    accreditation = models.CharField(
        max_length=200,
        blank=True,
        help_text='Laboratory accreditation (e.g., ISO, CAP)'
    )
    
    # Contact Information
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Primary phone number'
    )
    email = models.EmailField(
        blank=True,
        help_text='Laboratory email (can be different from user email)'
    )
    website = models.URLField(
        blank=True,
        help_text='Laboratory website URL'
    )
    
    # Description
    description = models.TextField(
        blank=True,
        help_text='Laboratory description and services offered'
    )
    
    # Verification Documents
    license_document = models.FileField(
        upload_to='laboratories/documents/licenses/',
        null=True,
        blank=True,
        help_text='Laboratory license document (PDF or image)'
    )
    accreditation_document = models.FileField(
        upload_to='laboratories/documents/accreditations/',
        null=True,
        blank=True,
        help_text='Accreditation certificate (PDF or image)'
    )
    
    # Status & Verification Flags
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether laboratory documents are verified'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether laboratory is currently available'
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
        db_table = 'laboratories'
        verbose_name = 'Laboratory'
        verbose_name_plural = 'Laboratories'
        indexes = [
            models.Index(fields=['lab_name']),
            models.Index(fields=['license_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return self.lab_name
