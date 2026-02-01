"""
Specialties models with multilingual support.
"""
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from providers.models.doctor import Doctor


class Specialty(models.Model):
    """
    Medical Specialty model.
    
    Supports multilingual content for title and description (en, ar, fr).
    The primary 'title' and 'description' fields are used as fallbacks.
    """
    # Primary title (used as fallback and for slug generation)
    title = models.CharField(
        max_length=255, 
        unique=True, 
        help_text='Primary title (English by default)'
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        db_index=True
    )
    
    # Multilingual titles
    title_en = models.CharField(
        max_length=255, 
        blank=True,
        default='',
        help_text='English title'
    )
    title_ar = models.CharField(
        max_length=255, 
        blank=True,
        default='',
        help_text='Arabic title'
    )
    title_fr = models.CharField(
        max_length=255, 
        blank=True,
        default='',
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
        default='',
        help_text='English description'
    )
    description_ar = models.TextField(
        blank=True,
        default='',
        help_text='Arabic description'
    )
    description_fr = models.TextField(
        blank=True,
        default='',
        help_text='French description'
    )
    
    # Categorization
    medical_domain = models.CharField(
        max_length=100, 
        blank=True,
        db_index=True,
        help_text='Medical domain (e.g., Surgery, Internal Medicine)'
    )
    icon = models.ImageField(
        upload_to='specialties/icons/', 
        null=True, 
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True
    )
    
    # SEO metadata
    meta_title = models.CharField(
        max_length=255, 
        blank=True,
        help_text='SEO meta title'
    )
    meta_description = models.TextField(
        blank=True,
        help_text='SEO meta description'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Specialty'
        verbose_name_plural = 'Specialties'
        ordering = ['title']
        indexes = [
            models.Index(fields=['is_active', 'medical_domain']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Auto-populate English fields from primary fields
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


class DoctorSpecialty(models.Model):
    """
    Relationship between Doctor and Specialty.
    """
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='doctor_specialties'
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.CASCADE,
        related_name='specialty_doctors'
    )
    is_primary = models.BooleanField(default=False)
    years_of_experience = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Doctor Specialty'
        verbose_name_plural = 'Doctor Specialties'
        unique_together = ['doctor', 'specialty']

    def __str__(self):
        return f"{self.doctor} - {self.specialty}"
