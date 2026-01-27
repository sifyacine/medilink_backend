"""
Social Media models with Generic Foreign Key support.
"""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class SocialMediaPlatform(models.TextChoices):
    """Supported social media platforms."""
    FACEBOOK = 'FACEBOOK', 'Facebook'
    INSTAGRAM = 'INSTAGRAM', 'Instagram'
    TWITTER = 'TWITTER', 'Twitter'
    LINKEDIN = 'LINKEDIN', 'LinkedIn'
    YOUTUBE = 'YOUTUBE', 'YouTube'
    TIKTOK = 'TIKTOK', 'TikTok'
    OTHER = 'OTHER', 'Other'


class SocialMediaLink(models.Model):
    """
    Generic Social Media Link model that can be attached to any other model.
    Uses Django's ContentType framework for Generic Foreign Keys.
    """
    # Generic Foreign Key fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Platform Information
    platform = models.CharField(
        max_length=50,
        choices=SocialMediaPlatform.choices,
        default=SocialMediaPlatform.FACEBOOK,
        help_text='Social media platform'
    )
    url = models.URLField(help_text='Full URL to the social profile')
    custom_label = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text='Custom label (required if platform is OTHER)'
    )
    
    # Display configuration
    is_visible = models.BooleanField(
        default=True,
        help_text='Whether to display this link publicly'
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text='Order in which links are displayed'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'social_media_links'
        verbose_name = 'Social Media Link'
        verbose_name_plural = 'Social Media Links'
        ordering = ['display_order', 'platform']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['platform']),
        ]

    def __str__(self):
        return f"{self.get_platform_display()}: {self.url}"
