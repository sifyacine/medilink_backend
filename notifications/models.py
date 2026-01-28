"""
Notification models for the Medilink platform.

This module provides a generic, reusable notification system that supports:
- In-app notifications with read/unread status
- Push notifications via FCM
- Related object references using Generic Foreign Keys
- Priority levels and notification types
- User notification preferences
"""
import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from accounts.models import User


class NotificationType(models.TextChoices):
    """Types of notifications."""
    # Appointment related
    APPOINTMENT_CREATED = 'APPOINTMENT_CREATED', 'Appointment Created'
    APPOINTMENT_CONFIRMED = 'APPOINTMENT_CONFIRMED', 'Appointment Confirmed'
    APPOINTMENT_CANCELLED = 'APPOINTMENT_CANCELLED', 'Appointment Cancelled'
    APPOINTMENT_UPDATED = 'APPOINTMENT_UPDATED', 'Appointment Updated'
    APPOINTMENT_REMINDER = 'APPOINTMENT_REMINDER', 'Appointment Reminder'
    APPOINTMENT_COMPLETED = 'APPOINTMENT_COMPLETED', 'Appointment Completed'
    
    # Account related
    ACCOUNT_VERIFIED = 'ACCOUNT_VERIFIED', 'Account Verified'
    ACCOUNT_SUSPENDED = 'ACCOUNT_SUSPENDED', 'Account Suspended'
    PROVIDER_APPROVED = 'PROVIDER_APPROVED', 'Provider Approved'
    PROVIDER_REFUSED = 'PROVIDER_REFUSED', 'Provider Refused'
    
    # Patient related
    PATIENT_RECORD_CREATED = 'PATIENT_RECORD_CREATED', 'Patient Record Created'
    PATIENT_ACCOUNT_LINKED = 'PATIENT_ACCOUNT_LINKED', 'Patient Account Linked'
    
    # System
    SYSTEM_ANNOUNCEMENT = 'SYSTEM_ANNOUNCEMENT', 'System Announcement'
    SYSTEM_MAINTENANCE = 'SYSTEM_MAINTENANCE', 'System Maintenance'
    
    # General
    MESSAGE = 'MESSAGE', 'Message'
    GENERAL = 'GENERAL', 'General Notification'


class NotificationPriority(models.TextChoices):
    """Priority levels for notifications."""
    LOW = 'LOW', 'Low'
    NORMAL = 'NORMAL', 'Normal'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'


class NotificationCategory(models.TextChoices):
    """Categories for grouping notifications."""
    APPOINTMENTS = 'APPOINTMENTS', 'Appointments'
    ACCOUNT = 'ACCOUNT', 'Account'
    MESSAGES = 'MESSAGES', 'Messages'
    SYSTEM = 'SYSTEM', 'System'
    PROMOTIONS = 'PROMOTIONS', 'Promotions'
    REMINDERS = 'REMINDERS', 'Reminders'


class Notification(models.Model):
    """
    Generic notification model for all types of notifications.
    
    Supports linking to any related object via Generic Foreign Key.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Recipient
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='User who receives this notification'
    )
    
    # Notification content
    title = models.CharField(
        max_length=255,
        help_text='Notification title'
    )
    message = models.TextField(
        help_text='Notification message/body'
    )
    
    # Optional image for rich notifications
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text='Image URL for rich notifications'
    )
    
    # Type, category, and priority
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        db_index=True,
        help_text='Type of notification'
    )
    category = models.CharField(
        max_length=20,
        choices=NotificationCategory.choices,
        default=NotificationCategory.SYSTEM,
        db_index=True,
        help_text='Category for grouping'
    )
    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        db_index=True,
        help_text='Priority level'
    )
    
    # Generic Foreign Key for related object
    related_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Content type of related object'
    )
    related_object_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='ID of related object (supports UUID and integer IDs)'
    )
    related_object = GenericForeignKey('related_content_type', 'related_object_id')
    
    # Status
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether the notification has been read'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the notification was read'
    )
    
    # Push notification status
    push_sent = models.BooleanField(
        default=False,
        help_text='Whether push notification was sent'
    )
    push_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When push notification was sent'
    )
    
    # Optional action URL (for frontend navigation)
    action_url = models.CharField(
        max_length=500,
        blank=True,
        help_text='URL/route to navigate when notification is clicked'
    )
    
    # Metadata
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional JSON data for the notification'
    )
    
    # Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='When this notification expires and should be auto-deleted'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When the notification was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'category']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['related_content_type', 'related_object_id']),
        ]
    
    def __str__(self):
        return f'{self.notification_type}: {self.title} -> {self.recipient.email}'
    
    def mark_as_read(self):
        """Mark the notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    def mark_as_unread(self):
        """Mark the notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    @property
    def is_expired(self):
        """Check if notification has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @classmethod
    def get_unread_count(cls, user):
        """Get unread notification count for a user."""
        return cls.objects.filter(recipient=user, is_read=False).count()
    
    @classmethod
    def cleanup_expired(cls):
        """Delete all expired notifications."""
        return cls.objects.filter(expires_at__lt=timezone.now()).delete()


class DeviceToken(models.Model):
    """
    Device tokens for push notifications.
    Stores FCM/APNs tokens for mobile and web push notifications.
    """
    DEVICE_TYPES = (
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    )
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='device_tokens',
        help_text='User who owns this device'
    )
    token = models.CharField(
        max_length=500,
        unique=True,
        help_text='FCM/APNs device token'
    )
    device_type = models.CharField(
        max_length=10,
        choices=DEVICE_TYPES,
        help_text='Type of device'
    )
    device_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Device name/model (optional)'
    )
    device_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Unique device identifier'
    )
    app_version = models.CharField(
        max_length=50,
        blank=True,
        help_text='App version when token was registered'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether this token is active'
    )
    failure_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of consecutive push failures'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time this token was used for push'
    )
    
    class Meta:
        db_table = 'device_tokens'
        verbose_name = 'Device Token'
        verbose_name_plural = 'Device Tokens'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_type']),
        ]
    
    def __str__(self):
        return f'{self.user.email} - {self.device_type}'
    
    def increment_failure(self):
        """Increment failure count and deactivate if too many failures."""
        self.failure_count += 1
        if self.failure_count >= 3:
            self.is_active = False
        self.save(update_fields=['failure_count', 'is_active', 'updated_at'])
    
    def reset_failures(self):
        """Reset failure count on successful push."""
        if self.failure_count > 0:
            self.failure_count = 0
            self.last_used_at = timezone.now()
            self.save(update_fields=['failure_count', 'last_used_at', 'updated_at'])


class NotificationPreference(models.Model):
    """
    User preferences for notifications.
    Controls which types of notifications a user wants to receive.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Push notification toggles
    push_enabled = models.BooleanField(
        default=True,
        help_text='Master toggle for push notifications'
    )
    push_appointments = models.BooleanField(
        default=True,
        help_text='Push for appointment notifications'
    )
    push_messages = models.BooleanField(
        default=True,
        help_text='Push for message notifications'
    )
    push_reminders = models.BooleanField(
        default=True,
        help_text='Push for reminder notifications'
    )
    push_promotions = models.BooleanField(
        default=False,
        help_text='Push for promotional notifications'
    )
    push_system = models.BooleanField(
        default=True,
        help_text='Push for system notifications'
    )
    
    # Email notification toggles
    email_enabled = models.BooleanField(
        default=True,
        help_text='Master toggle for email notifications'
    )
    email_appointments = models.BooleanField(
        default=True,
        help_text='Email for appointment notifications'
    )
    email_reminders = models.BooleanField(
        default=True,
        help_text='Email for reminder notifications'
    )
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(
        default=False,
        help_text='Enable quiet hours'
    )
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text='Start of quiet hours (no push)'
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text='End of quiet hours'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f'Preferences for {self.user.email}'
    
    def should_send_push(self, category: str) -> bool:
        """Check if push should be sent for a category."""
        if not self.push_enabled:
            return False
        
        category_map = {
            NotificationCategory.APPOINTMENTS: self.push_appointments,
            NotificationCategory.MESSAGES: self.push_messages,
            NotificationCategory.REMINDERS: self.push_reminders,
            NotificationCategory.PROMOTIONS: self.push_promotions,
            NotificationCategory.SYSTEM: self.push_system,
            NotificationCategory.ACCOUNT: True,
        }
        return category_map.get(category, True)
    
    def is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.localtime().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end
