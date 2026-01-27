"""
Comprehensive Nurse model for healthcare marketplace.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from providers.models.provider import Provider
from providers.models.doctor import Gender


class Nurse(models.Model):
    """
    Comprehensive Nurse profile model.
    Extends base Provider with detailed professional information.
    """
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='nurse_profile',
        help_text='Base provider profile'
    )
    
    # Personal Information
    first_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Nurse first name'
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Nurse last name'
    )
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True,
        help_text='Gender'
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text='Date of birth'
    )
    profile_image = models.ImageField(
        upload_to='nurses/profiles/',
        null=True,
        blank=True,
        help_text='Profile image'
    )
    
    # Professional Information
    license_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        blank=True,
        help_text='Nursing license number (unique)'
    )
    certification = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nursing certification type'
    )
    years_of_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Years of nursing experience'
    )
    biography = models.TextField(
        blank=True,
        help_text='Professional biography'
    )
    
    # Verification Documents
    degree_document = models.FileField(
        upload_to='nurses/documents/degrees/',
        null=True,
        blank=True,
        help_text='Nursing degree document (PDF or image)'
    )
    
    # Entrepreneur Card (Required for Nurses)
    entrepreneur_card_front = models.ImageField(
        upload_to='nurses/documents/entrepreneur_cards/',
        null=True,
        blank=True,
        help_text='Entrepreneur card front image'
    )
    entrepreneur_card_back = models.ImageField(
        upload_to='nurses/documents/entrepreneur_cards/',
        null=True,
        blank=True,
        help_text='Entrepreneur card back image'
    )
    entrepreneur_card_pdf = models.FileField(
        upload_to='nurses/documents/entrepreneur_cards/',
        null=True,
        blank=True,
        help_text='Entrepreneur card PDF version'
    )
    
    # Status & Verification Flags
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether nurse documents are verified'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether nurse is currently available for appointments'
    )
    is_home_service_available = models.BooleanField(
        default=True,
        help_text='Whether nurse provides home visits (common for nurses)'
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
        db_table = 'nurses'
        verbose_name = 'Nurse'
        verbose_name_plural = 'Nurses'
        indexes = [
            models.Index(fields=['license_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f'Nurse {self.first_name} {self.last_name}'
    
    @property
    def full_name(self):
        """Return full name."""
        return f'{self.first_name} {self.last_name}'


class NurseCertification(models.Model):
    """
    Optional certifications for nurses.
    A nurse can have multiple certifications.
    """
    nurse = models.ForeignKey(
        Nurse,
        on_delete=models.CASCADE,
        related_name='certifications',
        help_text='Nurse who holds this certification'
    )
    title = models.CharField(
        max_length=200,
        help_text='Certification title'
    )
    issuing_organization = models.CharField(
        max_length=200,
        blank=True,
        help_text='Organization that issued the certification'
    )
    issue_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date certification was issued'
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date certification expires (if applicable)'
    )
    certificate_document = models.FileField(
        upload_to='nurses/certifications/',
        null=True,
        blank=True,
        help_text='Certificate document (PDF or image)'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether certification is verified'
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    
    class Meta:
        db_table = 'nurse_certifications'
        verbose_name = 'Nurse Certification'
        verbose_name_plural = 'Nurse Certifications'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f'{self.nurse.full_name} - {self.title}'
