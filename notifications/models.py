import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================
# ENUMS / CHOICES
# ============================================

class NotificationType(models.TextChoices):
    """Types of notifications in the system"""
    # Appointments
    APPOINTMENT_CREATED = 'APPOINTMENT_CREATED', 'Appointment Created'
    APPOINTMENT_CONFIRMED = 'APPOINTMENT_CONFIRMED', 'Appointment Confirmed'
    APPOINTMENT_CANCELLED = 'APPOINTMENT_CANCELLED', 'Appointment Cancelled'
    APPOINTMENT_UPDATED = 'APPOINTMENT_UPDATED', 'Appointment Updated'
    APPOINTMENT_REMINDER = 'APPOINTMENT_REMINDER', 'Appointment Reminder'
    APPOINTMENT_COMPLETED = 'APPOINTMENT_COMPLETED', 'Appointment Completed'
    
    # Prescriptions
    PRESCRIPTION_ISSUED = 'PRESCRIPTION_ISSUED', 'Prescription Issued'
    PRESCRIPTION_RENEWED = 'PRESCRIPTION_RENEWED', 'Prescription Renewed'
    
    # Invoices
    INVOICE_CREATED = 'INVOICE_CREATED', 'Invoice Created'
    INVOICE_PAID = 'INVOICE_PAID', 'Invoice Paid'
    INVOICE_OVERDUE = 'INVOICE_OVERDUE', 'Invoice Overdue'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'
    
    # Nurse Requests
    NURSE_REQUEST_NEW = 'NURSE_REQUEST_NEW', 'New Nurse Request'
    NURSE_REQUEST_ACCEPTED = 'NURSE_REQUEST_ACCEPTED', 'Nurse Request Accepted'
    NURSE_REQUEST_COMPLETED = 'NURSE_REQUEST_COMPLETED', 'Nurse Request Completed'
    NURSE_REQUEST_CANCELLED = 'NURSE_REQUEST_CANCELLED', 'Nurse Request Cancelled'
    
    # Medical Records
    MEDICAL_RECORD_SHARED = 'MEDICAL_RECORD_SHARED', 'Medical Record Shared'
    LAB_RESULTS_READY = 'LAB_RESULTS_READY', 'Lab Results Ready'
    
    # General
    SYSTEM = 'SYSTEM', 'System Notification'
    MESSAGE = 'MESSAGE', 'Message'
    GENERAL = 'GENERAL', 'General'


class NotificationPriority(models.TextChoices):
    """Priority levels for notifications"""
    LOW = 'LOW', 'Low'
    NORMAL = 'NORMAL', 'Normal'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'


class NotificationCategory(models.TextChoices):
    """Categories for grouping notifications"""
    APPOINTMENTS = 'APPOINTMENTS', 'Appointments'
    PRESCRIPTIONS = 'PRESCRIPTIONS', 'Prescriptions'
    INVOICES = 'INVOICES', 'Invoices'
    NURSE_REQUESTS = 'NURSE_REQUESTS', 'Nurse Requests'
    MEDICAL_RECORDS = 'MEDICAL_RECORDS', 'Medical Records'
    MESSAGES = 'MESSAGES', 'Messages'
    SYSTEM = 'SYSTEM', 'System'
    GENERAL = 'GENERAL', 'General'


# ============================================
# MODELS
# ============================================

class DeviceToken(models.Model):
    """
    Stores FCM device tokens for push notifications.
    
    Each user can have multiple devices (phone, tablet, web browser).
    Tokens are automatically deactivated when they become invalid.
    Uses UUID primary key for compatibility with existing production databases.
    """
    DEVICE_TYPES = (
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.CharField(max_length=255)
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'token')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.device_type} ({'active' if self.is_active else 'inactive'})"


class Notification(models.Model):
    """
    Stores persistent notification history for users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(
        max_length=50, 
        choices=NotificationType.choices,
        default=NotificationType.GENERAL
    )
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL
    )
    category = models.CharField(
        max_length=50,
        choices=NotificationCategory.choices,
        default=NotificationCategory.GENERAL
    )
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} to {self.recipient.email}"