"""
Signals for the appointments app.

Creates notifications when appointment events occur.
Automatically adds patients to provider's patient list on confirmation.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Appointment, AppointmentStatus
from notifications.services import NotificationService
from notifications.models import NotificationType, NotificationPriority


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
    """
    if created:
        _notify_appointment_created(instance)
    else:
        previous_status = _previous_status.get(instance.pk)
        current_status = instance.status
        
        if previous_status != current_status:
            _notify_status_change(instance, previous_status, current_status)
        
        # Cleanup
        if instance.pk in _previous_status:
            del _previous_status[instance.pk]


def _notify_appointment_created(appointment):
    """
    Send notifications when a new appointment is created.
    
    Notifies:
    - Provider when a patient books
    - Patient when a provider creates the appointment
    """
    created_by = appointment.created_by
    provider_user = appointment.provider.user
    patient_user = appointment.patient_user
    
    # Get patient name for notification message
    patient_name = appointment.get_patient_display_name()
    provider_name = provider_user.get_full_name() or provider_user.email
    
    date_str = appointment.scheduled_date.strftime('%B %d, %Y')
    time_str = appointment.scheduled_time.strftime('%I:%M %p')
    
    # If patient created the appointment, notify the provider
    if created_by and created_by != provider_user:
        NotificationService.create_for_object(
            recipient=provider_user,
            title='New Appointment Request',
            message=f'{patient_name} has requested an appointment on {date_str} at {time_str}.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_CREATED,
            priority=NotificationPriority.HIGH,
            action_url=f'/appointments/{appointment.pk}'
        )
    
    # If provider created the appointment, notify the patient (if they have an account)
    if patient_user and created_by and created_by == provider_user:
        NotificationService.create_for_object(
            recipient=patient_user,
            title='New Appointment Scheduled',
            message=f'An appointment has been scheduled with {provider_name} on {date_str} at {time_str}.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_CREATED,
            priority=NotificationPriority.HIGH,
            action_url=f'/appointments/{appointment.pk}'
        )


def _notify_status_change(appointment, old_status, new_status):
    """
    Send notifications when appointment status changes.
    """
    provider_user = appointment.provider.user
    patient_user = appointment.patient_user
    
    patient_name = appointment.get_patient_display_name()
    provider_name = provider_user.get_full_name() or provider_user.email
    
    date_str = appointment.scheduled_date.strftime('%B %d, %Y')
    time_str = appointment.scheduled_time.strftime('%I:%M %p')
    
    if new_status == AppointmentStatus.CONFIRMED:
        # Notify patient that appointment is confirmed
        if patient_user:
            NotificationService.create_for_object(
                recipient=patient_user,
                title='Appointment Confirmed',
                message=f'Your appointment with {provider_name} on {date_str} at {time_str} has been confirmed.',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_CONFIRMED,
                priority=NotificationPriority.HIGH,
                action_url=f'/appointments/{appointment.pk}'
            )
        
        # IMPORTANT: Add patient to provider's patient list on confirmation
        _add_patient_to_provider_list(appointment)
    
    elif new_status == AppointmentStatus.CANCELLED:
        cancelled_by = appointment.cancelled_by
        reason = appointment.cancellation_notes or appointment.get_cancellation_reason_display()
        
        # Notify the other party about cancellation
        if cancelled_by == patient_user:
            # Patient cancelled, notify provider
            NotificationService.create_for_object(
                recipient=provider_user,
                title='Appointment Cancelled',
                message=f'{patient_name} has cancelled their appointment on {date_str}. Reason: {reason}',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_CANCELLED,
                priority=NotificationPriority.HIGH,
                action_url=f'/appointments/{appointment.pk}'
            )
        elif cancelled_by == provider_user:
            # Provider cancelled, notify patient
            if patient_user:
                NotificationService.create_for_object(
                    recipient=patient_user,
                    title='Appointment Cancelled',
                    message=f'Your appointment with {provider_name} on {date_str} has been cancelled. Reason: {reason}',
                    related_object=appointment,
                    notification_type=NotificationType.APPOINTMENT_CANCELLED,
                    priority=NotificationPriority.HIGH,
                    action_url=f'/appointments/{appointment.pk}'
                )
        else:
            # Admin or system cancelled, notify both
            NotificationService.create_for_object(
                recipient=provider_user,
                title='Appointment Cancelled',
                message=f'The appointment with {patient_name} on {date_str} has been cancelled.',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_CANCELLED,
                priority=NotificationPriority.NORMAL,
                action_url=f'/appointments/{appointment.pk}'
            )
            if patient_user:
                NotificationService.create_for_object(
                    recipient=patient_user,
                    title='Appointment Cancelled',
                    message=f'Your appointment with {provider_name} on {date_str} has been cancelled.',
                    related_object=appointment,
                    notification_type=NotificationType.APPOINTMENT_CANCELLED,
                    priority=NotificationPriority.NORMAL,
                    action_url=f'/appointments/{appointment.pk}'
                )
    
    elif new_status == AppointmentStatus.COMPLETED:
        # Notify patient that appointment is completed (for their records)
        if patient_user:
            NotificationService.create_for_object(
                recipient=patient_user,
                title='Appointment Completed',
                message=f'Your appointment with {provider_name} on {date_str} has been completed.',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_COMPLETED,
                priority=NotificationPriority.NORMAL,
                action_url=f'/appointments/{appointment.pk}'
            )
    
    elif new_status == AppointmentStatus.RESCHEDULED:
        # Both parties should be notified
        NotificationService.create_for_object(
            recipient=provider_user,
            title='Appointment Rescheduled',
            message=f'The appointment with {patient_name} has been rescheduled to {date_str} at {time_str}.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_UPDATED,
            priority=NotificationPriority.HIGH,
            action_url=f'/appointments/{appointment.pk}'
        )
        if patient_user:
            NotificationService.create_for_object(
                recipient=patient_user,
                title='Appointment Rescheduled',
                message=f'Your appointment with {provider_name} has been rescheduled to {date_str} at {time_str}.',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_UPDATED,
                priority=NotificationPriority.HIGH,
                action_url=f'/appointments/{appointment.pk}'
            )
        
        # IMPORTANT: Add patient to provider's patient list on reschedule (if not already)
        _add_patient_to_provider_list(appointment)


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
