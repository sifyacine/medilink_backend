"""
Comprehensive Seller model for healthcare marketplace.
"""
from django.db import models
from django.utils import timezone

from providers.models.provider import Provider


class Seller(models.Model):
    """
    Comprehensive Seller profile model.
    Extends base Provider with detailed seller/business information.
    """
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name='seller_profile',
        help_text='Base provider profile'
    )
    
    # Business Information
    business_name = models.CharField(
        max_length=200,
        db_index=True,
        blank=True,
        help_text='Business/company name'
    )
    tax_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        blank=True,
        help_text='Tax identification number (unique)'
    )
    business_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='Type of business (e.g., Medical Supplies, Pharmaceuticals)'
    )
    
    # Contact Information
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Primary phone number'
    )
    email = models.EmailField(
        blank=True,
        help_text='Business email (can be different from user email)'
    )
    website = models.URLField(
        blank=True,
        help_text='Business website URL'
    )
    
    # Description
    description = models.TextField(
        blank=True,
        help_text='Business description and products/services offered'
    )
    
    # Verification Documents
    business_license = models.FileField(
        upload_to='sellers/documents/licenses/',
        null=True,
        blank=True,
        help_text='Business license document (PDF or image)'
    )
    tax_certificate = models.FileField(
        upload_to='sellers/documents/tax/',
        null=True,
        blank=True,
        help_text='Tax certificate document (PDF or image)'
    )
    
    # Status & Verification Flags
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether seller documents are verified'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether seller is currently available'
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
        db_table = 'sellers'
        verbose_name = 'Seller'
        verbose_name_plural = 'Sellers'
        indexes = [
            models.Index(fields=['business_name']),
            models.Index(fields=['tax_id']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return self.business_name
