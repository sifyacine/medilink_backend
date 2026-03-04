"""
Appointment notification helpers.

Provides real-time appointment notifications via:
- WebSocket for instant browser updates
- FCM Push for mobile and web push notifications
- In-app notifications stored in database
"""
import logging
from typing import Optional, Dict, Any
from django.utils import timezone

from notifications.services import NotificationService, WebSocketBroadcaster
from notifications.models import NotificationType, NotificationPriority, NotificationCategory

logger = logging.getLogger(__name__)


def _get_provider_display_name(provider_user) -> str:
    """Get provider display name, never falling back to email."""
    name = provider_user.get_full_name()
    if name and name.strip():
        return name.strip()
    return 'Your healthcare provider'


class AppointmentNotifier:
    """
    Handles all appointment-related notifications for ALL provider types.
    
    Supports: Doctors, Nurses, Clinics, Laboratories, VTC, and any other provider
    with appointment functionality.
    
    Providers receive instant notifications when:
    - Patient requests a new appointment
    - Patient cancels an appointment
    - Patient reschedules
    
    Patients receive notifications when:
    - Provider confirms appointment
    - Provider cancels/rejects
    - Appointment reminders
    """
    
    @classmethod
    def _broadcast_to_appointment_group(cls, appointment, message_type: str, data: dict) -> None:
        """
        Broadcast to the appointment-specific WebSocket group so that
        any client subscribed to ``ws/appointments/<id>/`` receives the event.
        """
        WebSocketBroadcaster.send_to_appointment(
            appointment_id=appointment.pk,
            message_type=message_type,
            data=data,
        )

    @classmethod
    def _serialize_appointment_for_websocket(cls, appointment) -> Dict[str, Any]:
        """
        Serialize appointment for WebSocket transmission using the **full**
        ``AppointmentDetailSerializer`` so connected clients can update their
        UI state in-place without re-fetching from the REST API.

        The serializer runs without a request context, so ``allowed_actions``
        reflects generic status-based transitions (no user-specific permission
        filtering).  The frontend can refine actions locally if needed.
        """
        from .serializers import AppointmentDetailSerializer

        serializer = AppointmentDetailSerializer(appointment)
        return serializer.data
    
    @classmethod
    def notify_new_appointment(cls, appointment, created_by=None):
        """
        Send notifications when a new appointment is created.
        
        Args:
            appointment: The Appointment instance
            created_by: User who created the appointment (to avoid notifying themselves)
        """
        from common.utils import get_patient_display_name

        provider_user = appointment.provider.user
        patient_user = appointment.patient_user

        patient_name = get_patient_display_name(
            patient_user=appointment.patient_user, 
            patient_record=appointment.patient_record
        )
        provider_name = _get_provider_display_name(provider_user)

        date_str = appointment.scheduled_date.strftime('%B %d, %Y') if appointment.scheduled_date else "TBD"
        time_str = appointment.scheduled_time.strftime('%I:%M %p') if appointment.scheduled_time else "TBD"

        appointment_data = cls._serialize_appointment_for_websocket(appointment)

        # Create in-app notification + FCM push
        NotificationService.create_for_object(
            recipient=provider_user,
            title='🗓️ New Appointment Request',
            message=f'{patient_name} has requested an appointment on {date_str} at {time_str}.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_CREATED,
            priority=NotificationPriority.HIGH,
            action_url=f'/appointments/{appointment.pk}',
            data={'appointment_id': str(appointment.pk)},
        )

        # Also broadcast via appointment WebSocket for instant dashboard update
        ws_data = {
            'appointment': appointment_data,
            'message': f'New appointment request from {patient_name}',
        }
        WebSocketBroadcaster.send_to_provider(
            provider_id=appointment.provider.id,
            message_type='new_appointment',
            data=ws_data,
        )
        cls._broadcast_to_appointment_group(appointment, 'new_appointment', ws_data)

        # Notify patient if provider created the appointment
        if patient_user and created_by and created_by == provider_user:
            NotificationService.create_for_object(
                recipient=patient_user,
                title='🗓️ Appointment Scheduled',
                message=f'An appointment has been scheduled with {provider_name} on {date_str} at {time_str}.',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_CREATED,
                priority=NotificationPriority.HIGH,
                action_url=f'/appointments/{appointment.pk}',
                data={'appointment_id': str(appointment.pk)},
            )

            # WebSocket for patient
            ws_data_patient = {
                'appointment': appointment_data,
                'message': f'Appointment scheduled with {provider_name}',
            }
            WebSocketBroadcaster.send_to_patient(
                user_id=patient_user.id,
                message_type='new_appointment',
                data=ws_data_patient,
            )
            cls._broadcast_to_appointment_group(appointment, 'new_appointment', ws_data_patient)
    
    @classmethod
    def notify_appointment_confirmed(cls, appointment):
        """Send notification when appointment is confirmed."""
        from common.utils import get_patient_display_name
        
        patient_user = appointment.patient_user
        if not patient_user:
            return
        
        provider_name = _get_provider_display_name(appointment.provider.user)
        patient_name = get_patient_display_name(
            patient_user=appointment.patient_user,
            patient_record=appointment.patient_record
        )
        date_str = appointment.scheduled_date.strftime('%B %d, %Y') if appointment.scheduled_date else "TBD"
        time_str = appointment.scheduled_time.strftime('%I:%M %p') if appointment.scheduled_time else "TBD"
        
        # Create notification for patient
        NotificationService.create_for_object(
            recipient=patient_user,
            title='✅ Appointment Confirmed',
            message=f'Your appointment with {provider_name} on {date_str} at {time_str} has been confirmed.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_CONFIRMED,
            priority=NotificationPriority.HIGH,
            action_url=f'/appointments/{appointment.pk}',
        )
        
        # WebSocket update
        appointment_data = cls._serialize_appointment_for_websocket(appointment)
        ws_data = {
            'appointment': appointment_data,
            'message': f'Your appointment with {provider_name} has been confirmed!',
        }
        WebSocketBroadcaster.send_to_patient(
            user_id=patient_user.id,
            message_type='appointment_confirmed',
            data=ws_data,
        )
        # Notify provider that they confirmed (for other open tabs/devices)
        NotificationService.create_for_object(
            recipient=appointment.provider.user,
            title='✅ Appointment Confirmed',
            message=f'You confirmed the appointment with {patient_name} on {date_str} at {time_str}.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_CONFIRMED,
            priority=NotificationPriority.NORMAL,
            action_url=f'/appointments/{appointment.pk}',
        )
        WebSocketBroadcaster.send_to_provider(
            provider_id=appointment.provider.id,
            message_type='appointment_confirmed',
            data={
                'appointment': appointment_data,
                'message': f'Appointment with {patient_name} confirmed',
            },
        )
        cls._broadcast_to_appointment_group(appointment, 'appointment_confirmed', ws_data)
    
    @classmethod
    def notify_appointment_cancelled(cls, appointment, cancelled_by, reason: str = None):
        """
        Send notifications when appointment is cancelled.
        
        Args:
            appointment: The Appointment instance
            cancelled_by: User who cancelled
            reason: Cancellation reason
        """
        from common.utils import get_patient_display_name
        
        provider_user = appointment.provider.user
        patient_user = appointment.patient_user
        patient_name = get_patient_display_name(
            patient_user=appointment.patient_user, 
            patient_record=appointment.patient_record
        )
        provider_name = _get_provider_display_name(provider_user)
        date_str = appointment.scheduled_date.strftime('%B %d, %Y') if appointment.scheduled_date else "TBD"
        
        reason_text = reason or 'No reason provided'
        appointment_data = cls._serialize_appointment_for_websocket(appointment)
        
        # If patient cancelled, notify provider
        if cancelled_by == patient_user:
            NotificationService.create_for_object(
                recipient=provider_user,
                title='❌ Appointment Cancelled',
                message=f'{patient_name} has cancelled their appointment on {date_str}. Reason: {reason_text}',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_CANCELLED,
                priority=NotificationPriority.HIGH,
                action_url=f'/appointments/{appointment.pk}',
            )
            
            ws_cancel_data = {
                'appointment_id': str(appointment.pk),
                'appointment': appointment_data,
                'cancelled_by': 'patient',
                'reason': reason_text,
                'message': f'{patient_name} cancelled the appointment',
            }
            WebSocketBroadcaster.send_to_provider(
                provider_id=appointment.provider.id,
                message_type='appointment_cancelled',
                data=ws_cancel_data,
            )
            cls._broadcast_to_appointment_group(appointment, 'appointment_cancelled', ws_cancel_data)
        
        # If provider cancelled, notify patient
        elif cancelled_by == provider_user:
            if patient_user:
                NotificationService.create_for_object(
                    recipient=patient_user,
                    title='❌ Appointment Cancelled',
                    message=f'Your appointment with {provider_name} on {date_str} has been cancelled. Reason: {reason_text}',
                    related_object=appointment,
                    notification_type=NotificationType.APPOINTMENT_CANCELLED,
                    priority=NotificationPriority.HIGH,
                    action_url=f'/appointments/{appointment.pk}',
                )
                
                ws_cancel_data_prov = {
                    'appointment_id': str(appointment.pk),
                    'appointment': appointment_data,
                    'cancelled_by': 'provider',
                    'reason': reason_text,
                    'message': f'{provider_name} cancelled the appointment',
                }
                WebSocketBroadcaster.send_to_patient(
                    user_id=patient_user.id,
                    message_type='appointment_cancelled',
                    data=ws_cancel_data_prov,
                )
                cls._broadcast_to_appointment_group(appointment, 'appointment_cancelled', ws_cancel_data_prov)

        # System/auto cancellation: notify both sides when possible
        else:
            ws_cancel_data_auto = {
                'appointment_id': str(appointment.pk),
                'appointment': appointment_data,
                'cancelled_by': 'system',
                'reason': reason_text,
                'message': 'Appointment auto-cancelled after the scheduled time elapsed.',
            }

            # Provider notification
            NotificationService.create_for_object(
                recipient=provider_user,
                title='❌ Appointment Auto-Cancelled',
                message=f'Appointment with {patient_name} on {date_str} auto-cancelled. Reason: {reason_text}',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_CANCELLED,
                priority=NotificationPriority.HIGH,
                action_url=f'/appointments/{appointment.pk}',
            )
            WebSocketBroadcaster.send_to_provider(
                provider_id=appointment.provider.id,
                message_type='appointment_cancelled',
                data=ws_cancel_data_auto,
            )

            # Patient notification (if a user exists)
            if patient_user:
                NotificationService.create_for_object(
                    recipient=patient_user,
                    title='❌ Appointment Auto-Cancelled',
                    message=f'Your appointment with {provider_name} on {date_str} auto-cancelled. Reason: {reason_text}',
                    related_object=appointment,
                    notification_type=NotificationType.APPOINTMENT_CANCELLED,
                    priority=NotificationPriority.HIGH,
                    action_url=f'/appointments/{appointment.pk}',
                )
                WebSocketBroadcaster.send_to_patient(
                    user_id=patient_user.id,
                    message_type='appointment_cancelled',
                    data=ws_cancel_data_auto,
                )

            cls._broadcast_to_appointment_group(appointment, 'appointment_cancelled', ws_cancel_data_auto)
    
    @classmethod
    def notify_appointment_rescheduled(cls, appointment, rescheduled_by=None):
        """Send notifications when appointment is rescheduled."""
        from common.utils import get_patient_display_name
        
        provider_user = appointment.provider.user
        patient_user = appointment.patient_user
        provider_name = _get_provider_display_name(provider_user)
        date_str = appointment.scheduled_date.strftime('%B %d, %Y') if appointment.scheduled_date else "TBD"
        time_str = appointment.scheduled_time.strftime('%I:%M %p') if appointment.scheduled_time else "TBD"
        
        # Determine names
        patient_name = get_patient_display_name(
            patient_user=appointment.patient_user, 
            patient_record=appointment.patient_record
        )
        
        appointment_data = cls._serialize_appointment_for_websocket(appointment)
        
        # Notify provider
        NotificationService.create_for_object(
            recipient=provider_user,
            title='📅 Appointment Rescheduled',
            message=f'Appointment with {patient_name} rescheduled to {date_str} at {time_str}.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_UPDATED,
            priority=NotificationPriority.HIGH,
            action_url=f'/appointments/{appointment.pk}',
        )
        
        ws_reschedule_data = {
            'appointment': appointment_data,
            'old_status': 'PENDING',
            'new_status': 'RESCHEDULED',
            'message': f'Appointment rescheduled to {date_str} at {time_str}',
        }
        WebSocketBroadcaster.send_to_provider(
            provider_id=appointment.provider.id,
            message_type='appointment_rescheduled',
            data=ws_reschedule_data,
        )
        cls._broadcast_to_appointment_group(appointment, 'appointment_rescheduled', ws_reschedule_data)
        
        # Notify patient
        if patient_user:
            NotificationService.create_for_object(
                recipient=patient_user,
                title='📅 Appointment Rescheduled',
                message=f'Your appointment with {provider_name} has been rescheduled to {date_str} at {time_str}.',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_UPDATED,
                priority=NotificationPriority.HIGH,
                action_url=f'/appointments/{appointment.pk}',
            )
            
            ws_resched_patient = {
                'appointment': appointment_data,
                'message': f'Appointment rescheduled to {date_str} at {time_str}',
            }
            WebSocketBroadcaster.send_to_patient(
                user_id=patient_user.id,
                message_type='appointment_rescheduled',
                data=ws_resched_patient,
            )
            cls._broadcast_to_appointment_group(appointment, 'appointment_rescheduled', ws_resched_patient)
    
    @classmethod
    def notify_appointment_reminder(cls, appointment, minutes_before: int = 30):
        """
        Send appointment reminder.
        
        Called by a scheduled task before the appointment.
        """
        patient_user = appointment.patient_user
        if not patient_user:
            return
        
        provider_name = _get_provider_display_name(appointment.provider.user)
        time_str = appointment.scheduled_time.strftime('%I:%M %p') if appointment.scheduled_time else "TBD"
        
        NotificationService.create_for_object(
            recipient=patient_user,
            title='⏰ Appointment Reminder',
            message=f'Your appointment with {provider_name} is in {minutes_before} minutes at {time_str}.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_REMINDER,
            priority=NotificationPriority.HIGH,
            action_url=f'/appointments/{appointment.pk}',
        )
        
        appointment_data = cls._serialize_appointment_for_websocket(appointment)
        WebSocketBroadcaster.send_to_patient(
            user_id=patient_user.id,
            message_type='appointment_reminder',
            data={
                'appointment': appointment_data,
                'minutes_until': minutes_before,
                'message': f'Your appointment is in {minutes_before} minutes',
            }
        )
    
    @classmethod
    def notify_appointment_completed(cls, appointment):
        """Send notification when appointment is marked as completed."""
        from common.utils import get_patient_display_name

        patient_user = appointment.patient_user
        provider_user = appointment.provider.user
        provider_name = _get_provider_display_name(provider_user)
        patient_name = get_patient_display_name(
            patient_user=appointment.patient_user,
            patient_record=appointment.patient_record
        )
        date_str = appointment.scheduled_date.strftime('%B %d, %Y') if appointment.scheduled_date else "TBD"
        appointment_data = cls._serialize_appointment_for_websocket(appointment)

        # Notify patient via FCM + WebSocket
        if patient_user:
            NotificationService.create_for_object(
                recipient=patient_user,
                title='✔️ Appointment Completed',
                message=f'Your appointment with {provider_name} on {date_str} has been completed. Thank you for visiting!',
                related_object=appointment,
                notification_type=NotificationType.APPOINTMENT_COMPLETED,
                priority=NotificationPriority.NORMAL,
                action_url=f'/appointments/{appointment.pk}',
            )

            ws_data = {
                'appointment': appointment_data,
                'message': f'Appointment with {provider_name} completed',
            }
            WebSocketBroadcaster.send_to_patient(
                user_id=patient_user.id,
                message_type='appointment_completed',
                data=ws_data,
            )

        # Notify provider
        NotificationService.create_for_object(
            recipient=provider_user,
            title='✔️ Appointment Completed',
            message=f'Your appointment with {patient_name} on {date_str} has been completed.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_COMPLETED,
            priority=NotificationPriority.NORMAL,
            action_url=f'/appointments/{appointment.pk}',
        )
        WebSocketBroadcaster.send_to_provider(
            provider_id=appointment.provider.id,
            message_type='appointment_completed',
            data={
                'appointment': appointment_data,
                'message': f'Appointment with {patient_name} completed',
            },
        )
        # Broadcast to appointment group
        cls._broadcast_to_appointment_group(appointment, 'appointment_completed', {
            'appointment': appointment_data,
            'message': 'Appointment completed',
        })

    @classmethod
    def notify_appointment_rejected(cls, appointment):
        """
        Send notifications when provider rejects an appointment request.

        Notifies the patient via FCM push + WebSocket.
        """
        from common.utils import get_patient_display_name

        patient_user = appointment.patient_user
        if not patient_user:
            return

        provider_name = _get_provider_display_name(appointment.provider.user)
        date_str = appointment.scheduled_date.strftime('%B %d, %Y') if appointment.scheduled_date else "TBD"
        reason = getattr(appointment, 'rejection_reason', '') or 'No reason provided'

        # FCM + DB notification
        NotificationService.create_for_object(
            recipient=patient_user,
            title='❌ Appointment Request Declined',
            message=f'Your appointment request with {provider_name} on {date_str} was not accepted. {reason}',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_CANCELLED,
            priority=NotificationPriority.HIGH,
            action_url=f'/appointments/{appointment.pk}',
            data={'appointment_id': str(appointment.pk), 'reason': reason},
        )

        # WebSocket
        appointment_data = cls._serialize_appointment_for_websocket(appointment)
        ws_data = {
            'appointment': appointment_data,
            'reason': reason,
            'message': f'{provider_name} declined your appointment request',
        }
        WebSocketBroadcaster.send_to_patient(
            user_id=patient_user.id,
            message_type='appointment_rejected',
            data=ws_data,
        )
        # Push to provider so their list/detail updates instantly
        WebSocketBroadcaster.send_to_provider(
            provider_id=appointment.provider.id,
            message_type='appointment_rejected',
            data={
                'appointment': appointment_data,
                'reason': reason,
                'message': f'You declined the appointment request',
            },
        )
        cls._broadcast_to_appointment_group(appointment, 'appointment_rejected', ws_data)

    @classmethod
    def notify_appointment_no_show(cls, appointment):
        """
        Send notifications when patient is marked as no-show.

        Notifies the patient via FCM push + WebSocket.
        """
        patient_user = appointment.patient_user
        if not patient_user:
            return

        provider_name = _get_provider_display_name(appointment.provider.user)
        date_str = appointment.scheduled_date.strftime('%B %d, %Y') if appointment.scheduled_date else "TBD"
        time_str = appointment.scheduled_time.strftime('%I:%M %p') if appointment.scheduled_time else "TBD"

        # FCM + DB notification
        NotificationService.create_for_object(
            recipient=patient_user,
            title='⚠️ Missed Appointment',
            message=f'You were marked as a no-show for your appointment with {provider_name} on {date_str} at {time_str}.',
            related_object=appointment,
            notification_type=NotificationType.APPOINTMENT_CANCELLED,
            priority=NotificationPriority.HIGH,
            action_url=f'/appointments/{appointment.pk}',
            data={'appointment_id': str(appointment.pk)},
        )

        # WebSocket
        appointment_data = cls._serialize_appointment_for_websocket(appointment)
        ws_data = {
            'appointment': appointment_data,
            'message': f'You were marked as no-show for your appointment with {provider_name}',
        }
        WebSocketBroadcaster.send_to_patient(
            user_id=patient_user.id,
            message_type='appointment_no_show',
            data=ws_data,
        )
        # Push to provider so their list/detail updates instantly
        WebSocketBroadcaster.send_to_provider(
            provider_id=appointment.provider.id,
            message_type='appointment_no_show',
            data={
                'appointment': appointment_data,
                'message': f'Appointment marked as no-show',
            },
        )
        cls._broadcast_to_appointment_group(appointment, 'appointment_no_show', ws_data)
