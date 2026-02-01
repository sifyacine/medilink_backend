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


class SupportedLanguage(models.TextChoices):
    """Supported languages for multilingual content."""
    ENGLISH = 'en', 'English'
    ARABIC = 'ar', 'Arabic'
    FRENCH = 'fr', 'French'


class Service(models.Model):
    """
    Service model for doctors and nurses.
    Services can be linked to specialties.
    
    Supports multilingual content for title and description (en, ar, fr).
    """
    # Primary title (used as fallback and for slug generation)
    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text='Primary title (English by default)'
    )
    slug = models.SlugField(
        max_length=200,
        db_index=True,
        help_text='URL-friendly identifier'
    )
    
    # Multilingual titles
    title_en = models.CharField(
        max_length=200,
        blank=True,
        help_text='English title'
    )
    title_ar = models.CharField(
        max_length=200,
        blank=True,
        help_text='Arabic title'
    )
    title_fr = models.CharField(
        max_length=200,
        blank=True,
        help_text='French title'
    )
    
    # Primary description (used as fallback)
    description = models.TextField(
        blank=True,
        help_text='Primary description (English by default)'
    )
    
    # Multilingual descriptions
    description_en = models.TextField(
        blank=True,
        help_text='English description'
    )
    description_ar = models.TextField(
        blank=True,
        help_text='Arabic description'
    )
    description_fr = models.TextField(
        blank=True,
        help_text='French description'
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
        # Auto-populate title_en from title if not set
        if not self.title_en and self.title:
            self.title_en = self.title
        if not self.description_en and self.description:
            self.description_en = self.description
        super().save(*args, **kwargs)
    
    def get_title(self, language: str = 'en') -> str:
        """
        Get localized title based on language preference.
        Falls back to primary title if translation not available.
        
        Args:
            language: Language code ('en', 'ar', 'fr')
            
        Returns:
            Localized title string
        """
        lang_map = {
            'en': self.title_en,
            'ar': self.title_ar,
            'fr': self.title_fr,
        }
        localized = lang_map.get(language, '')
        return localized if localized else self.title
    
    def get_description(self, language: str = 'en') -> str:
        """
        Get localized description based on language preference.
        Falls back to primary description if translation not available.
        
        Args:
            language: Language code ('en', 'ar', 'fr')
            
        Returns:
            Localized description string
        """
        lang_map = {
            'en': self.description_en,
            'ar': self.description_ar,
            'fr': self.description_fr,
        }
        localized = lang_map.get(language, '')
        return localized if localized else self.description
    
    def get_localized_data(self, language: str = 'en') -> dict:
        """
        Get all localized fields for a given language.
        
        Args:
            language: Language code ('en', 'ar', 'fr')
            
        Returns:
            Dict with localized title and description
        """
        return {
            'title': self.get_title(language),
            'description': self.get_description(language),
        }


class DoctorService(models.Model):
    """
    Many-to-many relationship between Doctors and Services.
    Allows doctors to offer services with custom pricing.
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
    custom_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Custom duration for this doctor (overrides service default)'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether doctor is currently offering this service'
    )
    # Additional service-specific notes
    notes = models.TextField(
        blank=True,
        help_text='Doctor-specific notes about this service'
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
    
    @property
    def effective_price(self):
        """Return custom price if set, otherwise service default."""
        return self.custom_price if self.custom_price is not None else self.service.price
    
    @property
    def effective_duration(self):
        """Return custom duration if set, otherwise service default."""
        return self.custom_duration_minutes if self.custom_duration_minutes else self.service.duration_minutes


class NurseService(models.Model):
    """
    Many-to-many relationship between Nurses and Services.
    Allows nurses to offer services with custom pricing for on-demand requests.
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
    custom_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Custom duration for this nurse (overrides service default)'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether nurse is currently offering this service'
    )
    # Additional service-specific notes
    notes = models.TextField(
        blank=True,
        help_text='Nurse-specific notes about this service'
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
    
    @property
    def effective_price(self):
        """Return custom price if set, otherwise service default."""
        return self.custom_price if self.custom_price is not None else self.service.price
    
    @property
    def effective_duration(self):
        """Return custom duration if set, otherwise service default."""
        return self.custom_duration_minutes if self.custom_duration_minutes else self.service.duration_minutes


class ProviderCustomService(models.Model):
    """
    Custom services created by providers (doctors).
    Allows providers to create their own specialized services.
    
    Example: A dentist creates "Teeth Whitening Premium" service
    """
    id = models.AutoField(primary_key=True)
    
    # Provider who created the service
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        related_name='custom_services',
        help_text='Provider who created this custom service'
    )
    
    # Service details - Primary fields
    title = models.CharField(
        max_length=200,
        help_text='Primary title (English by default)'
    )
    description = models.TextField(
        blank=True,
        help_text='Primary description (English by default)'
    )
    
    # Multilingual titles
    title_en = models.CharField(
        max_length=200,
        blank=True,
        help_text='English title'
    )
    title_ar = models.CharField(
        max_length=200,
        blank=True,
        help_text='Arabic title'
    )
    title_fr = models.CharField(
        max_length=200,
        blank=True,
        help_text='French title'
    )
    
    # Multilingual descriptions
    description_en = models.TextField(
        blank=True,
        help_text='English description'
    )
    description_ar = models.TextField(
        blank=True,
        help_text='Arabic description'
    )
    description_fr = models.TextField(
        blank=True,
        help_text='French description'
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Service price'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.DZD,
        help_text='Currency'
    )
    
    # Duration
    duration_minutes = models.PositiveIntegerField(
        help_text='Service duration in minutes'
    )
    
    # Category (link to parent specialty if applicable)
    specialty = models.ForeignKey(
        'specialties.Specialty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='custom_services',
        help_text='Related specialty'
    )
    
    # Availability
    is_active = models.BooleanField(
        default=True,
        help_text='Whether service is active'
    )
    is_home_service = models.BooleanField(
        default=False,
        help_text='Whether service can be provided at home'
    )
    is_online_available = models.BooleanField(
        default=False,
        help_text='Whether service can be provided online'
    )
    
    # Optional image
    image = models.ImageField(
        upload_to='custom_services/',
        null=True,
        blank=True,
        help_text='Service image'
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'provider_custom_services'
        verbose_name = 'Provider Custom Service'
        verbose_name_plural = 'Provider Custom Services'
        indexes = [
            models.Index(fields=['provider', 'is_active']),
            models.Index(fields=['specialty']),
        ]
    
    def __str__(self):
        return f'{self.provider} - {self.title}'
    
    def save(self, *args, **kwargs):
        """Auto-populate English fields from primary fields."""
        if not self.title_en and self.title:
            self.title_en = self.title
        if not self.description_en and self.description:
            self.description_en = self.description
        super().save(*args, **kwargs)
    
    def get_title(self, language: str = 'en') -> str:
        """Get localized title."""
        lang_map = {
            'en': self.title_en,
            'ar': self.title_ar,
            'fr': self.title_fr,
        }
        localized = lang_map.get(language, '')
        return localized if localized else self.title
    
    def get_description(self, language: str = 'en') -> str:
        """Get localized description."""
        lang_map = {
            'en': self.description_en,
            'ar': self.description_ar,
            'fr': self.description_fr,
        }
        localized = lang_map.get(language, '')
        return localized if localized else self.description
    
    def get_localized_data(self, language: str = 'en') -> dict:
        """Get all localized fields for a given language."""
        return {
            'title': self.get_title(language),
            'description': self.get_description(language),
        }
