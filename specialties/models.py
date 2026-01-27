"""
Specialties models.
"""
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from providers.models.doctor import Doctor


class Specialty(models.Model):
    """
    Medical Specialty model.
    """
    title = models.CharField(max_length=255, unique=True, help_text='English title (default)')
    title_ar = models.CharField(max_length=255, blank=True, null=True, help_text='Arabic title')
    title_fr = models.CharField(max_length=255, blank=True, null=True, help_text='French title')
    title_en = models.CharField(max_length=255, blank=True, null=True, help_text='English title')
    
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    
    description = models.TextField(blank=True, help_text='English description (default)')
    description_ar = models.TextField(blank=True, null=True, help_text='Arabic description')
    description_fr = models.TextField(blank=True, null=True, help_text='French description')
    description_en = models.TextField(blank=True, null=True, help_text='English description')
    
    medical_domain = models.CharField(max_length=100, blank=True)
    icon = models.ImageField(upload_to='specialties/icons/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Metadata for SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Specialty'
        verbose_name_plural = 'Specialties'
        ordering = ['title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


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
