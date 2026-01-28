"""
Signals for the Notifications app.

Automatically creates notification preferences for new users
and handles notification-related events.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from accounts.models import User
from .models import NotificationPreference


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences when a new user is created."""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(post_delete, sender=User)
def cleanup_notifications(sender, instance, **kwargs):
    """Clean up notifications when a user is deleted (cascades automatically)."""
    # This is handled by CASCADE, but we can add custom cleanup here if needed
    pass
