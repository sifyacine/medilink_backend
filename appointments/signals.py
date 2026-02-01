"""
Signals for the appointments app.

Creates real-time notifications when appointment events occur.
- WebSocket for instant browser updates
- FCM Push for mobile notifications
- In-app notifications stored in database

Automatically adds patients to provider's patient list on confirmation.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import logging

from .models import Appointment, AppointmentStatus
from .notifications import AppointmentNotifier

logger = logging.getLogger(__name__)


# Track status changes
_previous_status = {}


@receiver(pre_save, sender=Appointment)
def track_appointment_status_change(sender, instance, **kwargs):
    """Track status before save to detect changes."""
    if instance.pk:
        try:
            old_instance = Appointment.objects.get(pk=instance.pk)
            _previous_status[instance.pk] = old_instance.status
        except Appointment.DoesNotExist:
            _previous_status[instance.pk] = None
    else:
        _previous_status[instance.pk] = None


@receiver(post_save, sender=Appointment)
def handle_appointment_save(sender, instance, created, **kwargs):
    """
    Handle appointment save events and create appropriate notifications.
    
    Uses AppointmentNotifier for:
    - Real-time WebSocket delivery (doctor sees instantly)
    - FCM push notifications (mobile/web)
    - In-app notification storage
    """
    try:
        if created:
            # New appointment created
            AppointmentNotifier.notify_new_appointment(
                appointment=instance,
                created_by=instance.created_by
            )
        else:
            previous_status = _previous_status.get(instance.pk)
            current_status = instance.status
            
            if previous_status != current_status:
                _handle_status_change(instance, previous_status, current_status)
            
            # Cleanup
            if instance.pk in _previous_status:
                del _previous_status[instance.pk]
    except Exception as e:
        logger.error(f"Error handling appointment save signal: {e}")


def _handle_status_change(appointment, old_status, new_status):
    """
    Handle appointment status changes and send appropriate notifications.
    """
    try:
        if new_status == AppointmentStatus.CONFIRMED:
            AppointmentNotifier.notify_appointment_confirmed(appointment)
            _add_patient_to_provider_list(appointment)
        
        elif new_status == AppointmentStatus.CANCELLED:
            cancelled_by = appointment.cancelled_by
            reason = appointment.cancellation_notes or (
                appointment.get_cancellation_reason_display() 
                if hasattr(appointment, 'get_cancellation_reason_display') else None
            )
            AppointmentNotifier.notify_appointment_cancelled(
                appointment=appointment,
                cancelled_by=cancelled_by,
                reason=reason
            )
        
        elif new_status == AppointmentStatus.COMPLETED:
            AppointmentNotifier.notify_appointment_completed(appointment)
        
        elif new_status == AppointmentStatus.RESCHEDULED:
            AppointmentNotifier.notify_appointment_rescheduled(appointment)
            _add_patient_to_provider_list(appointment)
        
        elif new_status == AppointmentStatus.REJECTED:
            # Provider rejected the appointment request
            _notify_appointment_rejected(appointment)
        
    except Exception as e:
        logger.error(f"Error handling status change notification: {e}")


def _notify_appointment_rejected(appointment):
    """Notify patient that their appointment was rejected."""
    from notifications.services import NotificationService
    from notifications.models import NotificationType, NotificationPriority
    
    patient_user = appointment.patient_user
    if not patient_user:
        return
    
    provider_name = appointment.provider.user.get_full_name() or appointment.provider.user.email
    date_str = appointment.scheduled_date.strftime('%B %d, %Y')
    
    reason = appointment.rejection_notes if hasattr(appointment, 'rejection_notes') else 'No reason provided'
    
    NotificationService.create_for_object(
        recipient=patient_user,
        title='Appointment Request Declined',
        message=f'Your appointment request with {provider_name} on {date_str} was not accepted. {reason}',
        related_object=appointment,
        notification_type=NotificationType.APPOINTMENT_CANCELLED,
        priority=NotificationPriority.NORMAL,
        action_url=f'/appointments/{appointment.pk}',
    )


def _add_patient_to_provider_list(appointment):
    """
    Automatically add patient to provider's patient list when appointment is confirmed/rescheduled.
    
    This establishes a doctor-patient relationship:
    - Creates a PatientRecord if patient only has User account
    - Creates ProviderPatientAccess record for the relationship
    - Prevents duplicates
    """
    from patients.models import PatientRecord, ProviderPatientAccess
    from django.utils import timezone
    
    provider = appointment.provider
    
    # Case 1: Patient has a PatientRecord
    if appointment.patient_record:
        patient_record = appointment.patient_record
    # Case 2: Patient has a User account but no PatientRecord linked
    elif appointment.patient_user:
        # Check if user already has a linked patient record
        try:
            patient_record = PatientRecord.objects.get(linked_user=appointment.patient_user)
        except PatientRecord.DoesNotExist:
            # Create a patient record for this user
            user = appointment.patient_user
            patient_record = PatientRecord.objects.create(
                linked_user=user,
                first_name=user.get_full_name().split()[0] if user.get_full_name() else user.email.split('@')[0],
                last_name=user.get_full_name().split()[-1] if user.get_full_name() and len(user.get_full_name().split()) > 1 else '',
                date_of_birth=timezone.now().date(),  # Placeholder - should be updated by patient
                gender='PREFER_NOT_TO_SAY',
                phone_number='',
                email=user.email,
            )
    else:
        # No patient identification - cannot create access
        return
    
    # Create or update provider-patient access
    access, created = ProviderPatientAccess.objects.get_or_create(
        provider=provider,
        patient_record=patient_record,
        defaults={
            'access_level': 'FULL',
            'granted_by': provider,  # Self-granted via appointment
        }
    )
    
    if created:
        # Log this for audit purposes
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Patient {patient_record.patient_unique_id} added to provider "
            f"{provider.id}'s patient list via appointment {appointment.pk}"
        )
