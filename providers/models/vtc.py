"""
Comprehensive Healthcare VTC (Vehicle Transport Company) model.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from providers.models.provider import Provider


class VTC(models.Model):
    """
    Comprehensive Healthcare VTC profile model.
    Extends base Provider with detailed transport company information.
    """
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='vtc_profile',
        help_text='Base provider profile'
    )
    
    # Company Information
    company_name = models.CharField(
        max_length=200,
        db_index=True,
        blank=True,
        help_text='VTC company name'
    )
    license_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        blank=True,
        help_text='Transport license number (unique)'
    )
    
    # Contact Information
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Primary phone number'
    )
    email = models.EmailField(
        blank=True,
        help_text='Company email (can be different from user email)'
    )
    website = models.URLField(
        blank=True,
        help_text='Company website URL'
    )
    
    # Fleet Information
    fleet_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Number of vehicles in fleet'
    )
    vehicle_types = models.CharField(
        max_length=200,
        blank=True,
        help_text='Types of vehicles (e.g., Ambulance, Medical Van, Wheelchair Accessible)'
    )
    
    # Description
    description = models.TextField(
        blank=True,
        help_text='Company description and services offered'
    )
    
    # Verification Documents
    transport_license = models.FileField(
        upload_to='vtcs/documents/licenses/',
        null=True,
        blank=True,
        help_text='Transport license document (PDF or image)'
    )
    insurance_certificate = models.FileField(
        upload_to='vtcs/documents/insurance/',
        null=True,
        blank=True,
        help_text='Insurance certificate (PDF or image)'
    )
    
    # Status & Verification Flags
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether VTC documents are verified'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether VTC is currently available'
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
        db_table = 'vtcs'
        verbose_name = 'Healthcare VTC'
        verbose_name_plural = 'Healthcare VTCs'
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['license_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return self.company_name
