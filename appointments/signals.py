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
from django.db import transaction
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

    Uses transaction.on_commit() so that WebSocket broadcasts and FCM pushes
    fire AFTER the database transaction is committed — this prevents the
    frontend from fetching stale data when it receives the WS event.
    """
    # Capture values before the lambda closes over the mutable instance
    appointment_id = instance.pk
    is_created = created
    previous_status = _previous_status.pop(instance.pk, None)
    current_status = instance.status

    def _notify():
        try:
            # Re-fetch the appointment so any deferred fields are available
            fresh = Appointment.objects.select_related(
                'provider', 'patient_user', 'patient_record', 'service'
            ).get(pk=appointment_id)

            if is_created:
                AppointmentNotifier.notify_new_appointment(
                    appointment=fresh,
                    created_by=fresh.created_by,
                )
            else:
                if previous_status != current_status:
                    _handle_status_change(fresh, previous_status, current_status)
                else:
                    # Non-status field update (notes, meeting_link, services, etc.)
                    # Broadcast a lightweight WS event so open dashboards stay in sync.
                    _broadcast_generic_update(fresh)
        except Appointment.DoesNotExist:
            logger.warning("Appointment %s no longer exists, skipping notification", appointment_id)
        except Exception as e:
            logger.error("Error in post-commit appointment notification: %s", e)

    transaction.on_commit(_notify)


def _handle_status_change(appointment, old_status, new_status):
    """
    Handle appointment status changes and send appropriate notifications.
    
    Each status transition triggers:
    - FCM push notification (via NotificationService)
    - WebSocket broadcast to user groups + appointment group
    - In-app notification stored in DB
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
            AppointmentNotifier.notify_appointment_rejected(appointment)
        
        elif new_status == AppointmentStatus.NO_SHOW:
            AppointmentNotifier.notify_appointment_no_show(appointment)
        
    except Exception as e:
        logger.error(f"Error handling status change notification: {e}")


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


def _broadcast_generic_update(appointment):
    """
    Broadcast a lightweight ``appointment_updated`` WebSocket event when
    non-status fields change (e.g. notes, meeting_link, services).

    This keeps every open dashboard/detail page in sync without creating
    a full in-app notification.
    """
    from notifications.services import WebSocketBroadcaster

    try:
        data = AppointmentNotifier._serialize_appointment_for_websocket(appointment)
        ws_payload = {
            'appointment': data,
            'message': 'Appointment details updated',
        }

        # Push to provider
        WebSocketBroadcaster.send_to_provider(
            provider_id=appointment.provider.id,
            message_type='appointment_updated',
            data=ws_payload,
        )

        # Push to patient
        if appointment.patient_user:
            WebSocketBroadcaster.send_to_patient(
                user_id=appointment.patient_user.id,
                message_type='appointment_updated',
                data=ws_payload,
            )

        # Push to appointment-specific group
        WebSocketBroadcaster.send_to_appointment(
            appointment_id=appointment.pk,
            message_type='appointment_updated',
            data=ws_payload,
        )
    except Exception as e:
        logger.error("Error broadcasting generic appointment update: %s", e)
