"""
Services model for doctors and nurses.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.text import slugify


class Currency(models.TextChoices):
    """Currency choices."""
    DZD = 'DZD', 'Algerian Dinar'
    USD = 'USD', 'US Dollar'
    EUR = 'EUR', 'Euro'


class ServiceType(models.TextChoices):
    """Service type choices - determines which provider type can offer this service."""
    DOCTOR = 'DOCTOR', 'Doctor Service'
    NURSE = 'NURSE', 'Nursing Service'
    VTC = 'VTC', 'Health VTC Service'
    GENERAL = 'GENERAL', 'General Service'


class Service(models.Model):
    """
    Service model for doctors and nurses.
    Services can be linked to specialties.
    """
    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text='Service title'
    )
    slug = models.SlugField(
        max_length=200,
        db_index=True,
        help_text='URL-friendly identifier'
    )
    description = models.TextField(
        blank=True,
        help_text='Service description'
    )
    
    # Service Type - determines which provider type can offer this service
    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        default=ServiceType.GENERAL,
        db_index=True,
        help_text='Type of service (DOCTOR, NURSE, VTC, GENERAL)'
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Service price (base/minimum price for on-demand services)'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.DZD,
        help_text='Currency'
    )
    
    # Service Details
    duration_minutes = models.PositiveIntegerField(
        help_text='Service duration in minutes'
    )
    icon = models.ImageField(
        upload_to='services/icons/',
        null=True,
        blank=True,
        help_text='Service icon'
    )
    is_home_service = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether service can be provided at home'
    )
    # For on-demand nursing services
    is_on_demand = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether this service is available for on-demand requests (Uber-like flow)'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether service is active and available'
    )
    
    # Relationships (optional)
    specialty = models.ForeignKey(
        'specialties.Specialty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services',
        help_text='Related specialty (optional)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'services'
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_home_service']),
            models.Index(fields=['service_type', 'is_active']),
            models.Index(fields=['is_on_demand', 'service_type']),
        ]
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class DoctorService(models.Model):
    """
    Many-to-many relationship between Doctors and Services.
    """
    doctor = models.ForeignKey(
        'providers.Doctor',
        on_delete=models.CASCADE,
        related_name='services',
        help_text='Doctor offering this service'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='doctors',
        help_text='Service'
    )
    custom_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Custom price for this doctor (overrides service default)'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether doctor is currently offering this service'
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    
    class Meta:
        db_table = 'doctor_services'
        verbose_name = 'Doctor Service'
        verbose_name_plural = 'Doctor Services'
        unique_together = [['doctor', 'service']]
    
    def __str__(self):
        return f'{self.doctor.full_name} - {self.service.title}'


class NurseService(models.Model):
    """
    Many-to-many relationship between Nurses and Services.
    """
    nurse = models.ForeignKey(
        'providers.Nurse',
        on_delete=models.CASCADE,
        related_name='services',
        help_text='Nurse offering this service'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='nurses',
        help_text='Service'
    )
    custom_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Custom price for this nurse (overrides service default)'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether nurse is currently offering this service'
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    
    class Meta:
        db_table = 'nurse_services'
        verbose_name = 'Nurse Service'
        verbose_name_plural = 'Nurse Services'
        unique_together = [['nurse', 'service']]
    
    def __str__(self):
        return f'{self.nurse.full_name} - {self.service.title}'
