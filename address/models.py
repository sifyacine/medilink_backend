"""
Address models with Generic Foreign Key support.
"""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Address(models.Model):
    """
    Generic Address model that can be attached to any other model.
    Uses Django's ContentType framework for Generic Foreign Keys.
    """
    # Generic Foreign Key fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Address field data
    street = models.CharField(max_length=255, blank=True, help_text='Street address')
    city = models.CharField(max_length=100, blank=True, help_text='City')
    state = models.CharField(max_length=100, blank=True, help_text='State/Province')
    zip_code = models.CharField(max_length=20, blank=True, help_text='ZIP/Postal code')
    country = models.CharField(max_length=100, default='Algeria', help_text='Country')
    
    # Coordinates for mapping
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text='Latitude coordinate'
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text='Longitude coordinate'
    )
    
    # Status and Metadata
    is_primary = models.BooleanField(
        default=False, 
        help_text='Whether this is the primary address for the object'
    )
    address_type = models.CharField(
        max_length=20,
        choices=[
            ('HOME', 'Home'),
            ('WORK', 'Work'),
            ('CLINIC', 'Clinic'),
            ('HOSPITAL', 'Hospital'),
            ('OTHER', 'Other'),
        ],
        default='WORK',
        help_text='Type of address'
    )
    notes = models.TextField(blank=True, help_text='Optional notes about the address')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'addresses'
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['city']),
            models.Index(fields=['country']),
        ]

    def __str__(self):
        return f"{self.street}, {self.city}, {self.country}"
