"""
Comprehensive Doctor model for healthcare marketplace.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from providers.models.provider import Provider


class Gender(models.TextChoices):
    """Gender choices."""
    MALE = 'MALE', 'Male'
    FEMALE = 'FEMALE', 'Female'
    OTHER = 'OTHER', 'Other'
    PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY', 'Prefer not to say'


class Doctor(models.Model):
    """
    Comprehensive Doctor profile model.
    Extends base Provider with detailed professional information.
    """
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        help_text='Base provider profile'
    )
    
    # Personal Information
    first_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Doctor first name'
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Doctor last name'
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
        upload_to='doctors/profiles/',
        null=True,
        blank=True,
        help_text='Profile image'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Primary phone number for this doctor'
    )
    
    # Professional Information
    license_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Medical license number (unique when set)'
    )
    years_of_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Years of medical experience'
    )
    biography = models.TextField(
        blank=True,
        help_text='Professional biography'
    )
    
    # Verification Documents
    degree_document = models.FileField(
        upload_to='doctors/documents/degrees/',
        null=True,
        blank=True,
        help_text='Medical degree document (PDF or image)'
    )
    
    # Status & Verification Flags
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether doctor documents are verified'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether doctor is currently available for appointments'
    )
    is_home_service_available = models.BooleanField(
        default=False,
        help_text='Whether doctor provides home visits'
    )
    
    # ==========================================================================
    # CONSULTATION PRICING
    # ==========================================================================
    consultation_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Standard consultation price (clinic visit)'
    )
    home_visit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Home visit consultation price'
    )
    online_consultation_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Online/video consultation price'
    )
    currency = models.CharField(
        max_length=3,
        default='DZD',
        help_text='Currency for prices (default: Algerian Dinar)'
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
        db_table = 'doctors'
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
        indexes = [
            models.Index(fields=['license_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_available']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['license_number'],
                condition=models.Q(license_number__isnull=False),
                name='doctor_license_number_unique_notnull',
            ),
        ]
    
    def __str__(self):
        return f'Dr. {self.first_name} {self.last_name}'
    
    @property
    def full_name(self):
        """Return full name."""
        return f'{self.first_name} {self.last_name}'


class DoctorCertification(models.Model):
    """
    Optional certifications for doctors.
    A doctor can have multiple certifications.
    """
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='certifications',
        help_text='Doctor who holds this certification'
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
        upload_to='doctors/certifications/',
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
        db_table = 'doctor_certifications'
        verbose_name = 'Doctor Certification'
        verbose_name_plural = 'Doctor Certifications'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f'{self.doctor.full_name} - {self.title}'
