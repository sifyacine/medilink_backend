"""
Nurse-request notification helpers.

Provides real-time notifications via:
- WebSocket for instant browser/mobile updates
- FCM Push for background mobile notifications
- In-app notifications stored in database

Every notification method:
1. Creates a persistent Notification row (+ FCM push) via NotificationService
2. Broadcasts the full serialized request/offer via WebSocketBroadcaster
   so connected clients can update their state **without re-fetching**.
"""
import logging
from typing import Dict, Any

from notifications.services import NotificationService, WebSocketBroadcaster
from notifications.models import NotificationType, NotificationPriority

logger = logging.getLogger(__name__)


def _get_display_name(user) -> str:
    """Get user display name, never falling back to email."""
    name = user.get_full_name()
    if name and name.strip():
        return name.strip()
    return 'Your healthcare provider'


class NurseRequestNotifier:
    """
    Handles all on-demand nursing request notifications.

    Patient receives notifications when:
    - A nurse submits an offer (accept at patient price / counter-offer)
    - Their request is accepted & nurse is on the way
    - The service starts (in-progress)
    - The service is completed
    - The request is cancelled

    Nurse receives notifications when:
    - A new request appears in their area/service list
    - A patient accepts their offer
    - A patient cancels the request they responded to
    - The request is completed
    """

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    @classmethod
    def _serialize_request(cls, request_obj) -> Dict[str, Any]:
        """Return full NurseServiceRequestDetailSerializer output."""
        from .serializers import NurseServiceRequestDetailSerializer
        return NurseServiceRequestDetailSerializer(request_obj).data

    @classmethod
    def _serialize_offer(cls, offer) -> Dict[str, Any]:
        """Return full NurseOfferSerializer output."""
        from .serializers import NurseOfferSerializer
        return NurseOfferSerializer(offer).data

    # ------------------------------------------------------------------
    # Broadcast helpers
    # ------------------------------------------------------------------

    @classmethod
    def _ws_to_patient(cls, request_obj, message_type: str, data: dict):
        """Push a WS event to the patient who created the request."""
        patient_user = request_obj.get_patient_user()
        if patient_user:
            WebSocketBroadcaster.send_to_patient(
                user_id=patient_user.id,
                message_type=message_type,
                data=data,
            )

    @classmethod
    def _ws_to_nurse(cls, nurse_provider, message_type: str, data: dict):
        """Push a WS event to a specific nurse (provider)."""
        WebSocketBroadcaster.send_to_provider(
            provider_id=nurse_provider.id,
            message_type=message_type,
            data=data,
        )

    @classmethod
    def _ws_to_request_group(cls, request_obj, message_type: str, data: dict):
        """Broadcast to ``request_<id>_updates`` group."""
        group = f"request_{request_obj.pk}_updates"
        WebSocketBroadcaster.broadcast(
            channel=group,
            message_type=message_type,
            data=data,
        )

    @classmethod
    def _ws_to_city(cls, city: str, message_type: str, data: dict):
        """Broadcast to all nurses listening on a city channel."""
        group = f"city_{city.lower().replace(' ', '_')}_requests"
        WebSocketBroadcaster.broadcast(
            channel=group,
            message_type=message_type,
            data=data,
        )

    # ------------------------------------------------------------------
    # Notification events
    # ------------------------------------------------------------------

    @classmethod
    def notify_new_request(cls, request_obj):
        """
        Broadcast to nurses when a patient creates a new request.

        - City-wide WS broadcast so all online nurses see it
        - No in-app notification per nurse (too noisy) — WS only
        """
        data = cls._serialize_request(request_obj)
        ws_data = {
            'request': data,
            'message': f'New nursing request: {request_obj.service.title}',
        }

        # Broadcast to city channel
        cls._ws_to_city(request_obj.city, 'nurse_request_new', ws_data)

        # Also push to the request-specific group
        cls._ws_to_request_group(request_obj, 'nurse_request_new', ws_data)

        # Notify the patient too (confirmation)
        cls._ws_to_patient(request_obj, 'nurse_request_new', ws_data)

    @classmethod
    def notify_nurse_offer(cls, request_obj, offer):
        """
        Notify the patient when a nurse submits an offer (accept or counter-offer).
        """
        patient_user = request_obj.get_patient_user()
        if not patient_user:
            return

        offer_data = cls._serialize_offer(offer)
        request_data = cls._serialize_request(request_obj)
        nurse_name = offer_data.get('nurse_name', 'A nurse')
        is_counter = offer.offered_price > request_obj.patient_offered_price

        if is_counter:
            title = '💰 Counter Offer Received'
            message = (
                f'{nurse_name} offered ${offer.offered_price} for '
                f'{request_obj.service.title}.'
            )
            notif_type = NotificationType.NURSE_REQUEST_COUNTER_OFFER
        else:
            title = '🩺 Nurse Responded'
            message = (
                f'{nurse_name} accepted your request for '
                f'{request_obj.service.title} at ${offer.offered_price}.'
            )
            notif_type = NotificationType.NURSE_REQUEST_OFFER

        # In-app + FCM
        NotificationService.create_for_object(
            recipient=patient_user,
            title=title,
            message=message,
            related_object=request_obj,
            notification_type=notif_type,
            priority=NotificationPriority.HIGH,
            action_url=f'/nurse-requests/{request_obj.pk}',
            data={'request_id': str(request_obj.pk), 'offer_id': str(offer.pk)},
        )

        ws_data = {
            'request': request_data,
            'offer': offer_data,
            'message': message,
        }
        cls._ws_to_patient(request_obj, 'nurse_request_offer', ws_data)
        cls._ws_to_request_group(request_obj, 'nurse_request_offer', ws_data)

    @classmethod
    def notify_offer_accepted(cls, request_obj, accepted_offer):
        """
        Notify the nurse whose offer was accepted AND inform the patient.
        """
        request_data = cls._serialize_request(request_obj)
        patient_name = request_obj.get_patient_display_name()
        nurse_user = accepted_offer.nurse.user

        # --- Nurse notification ---
        NotificationService.create_for_object(
            recipient=nurse_user,
            title='✅ Your Offer Was Accepted',
            message=(
                f'{patient_name} accepted your offer for '
                f'{request_obj.service.title}. Final price: ${request_obj.final_price}.'
            ),
            related_object=request_obj,
            notification_type=NotificationType.NURSE_REQUEST_ACCEPTED,
            priority=NotificationPriority.HIGH,
            action_url=f'/nurse-requests/{request_obj.pk}',
            data={'request_id': str(request_obj.pk)},
        )

        ws_nurse = {
            'request': request_data,
            'message': f'{patient_name} accepted your offer',
        }
        cls._ws_to_nurse(accepted_offer.nurse, 'nurse_request_accepted', ws_nurse)

        cls._ws_to_request_group(request_obj, 'nurse_request_accepted', {
            'request': request_data,
            'message': 'Offer accepted',
        })

    @classmethod
    def notify_service_started(cls, request_obj):
        """
        Notify the patient when the nurse starts the service.
        """
        patient_user = request_obj.get_patient_user()
        if not patient_user:
            return

        request_data = cls._serialize_request(request_obj)
        nurse_name = ''
        if request_obj.accepted_nurse:
            nurse_name = _get_display_name(request_obj.accepted_nurse.user)

        NotificationService.create_for_object(
            recipient=patient_user,
            title='🏥 Service Started',
            message=f'{nurse_name} has started providing {request_obj.service.title}.',
            related_object=request_obj,
            notification_type=NotificationType.NURSE_REQUEST_IN_PROGRESS,
            priority=NotificationPriority.HIGH,
            action_url=f'/nurse-requests/{request_obj.pk}',
            data={'request_id': str(request_obj.pk)},
        )

        ws_data = {
            'request': request_data,
            'message': f'{nurse_name} has started the service',
        }
        cls._ws_to_patient(request_obj, 'nurse_request_in_progress', ws_data)
        cls._ws_to_nurse(request_obj.accepted_nurse, 'nurse_request_in_progress', ws_data)
        cls._ws_to_request_group(request_obj, 'nurse_request_in_progress', ws_data)

    @classmethod
    def notify_service_completed(cls, request_obj):
        """
        Notify the patient when service is completed (by nurse → no self-notification for nurse).
        """
        request_data = cls._serialize_request(request_obj)
        nurse_name = ''
        if request_obj.accepted_nurse:
            nurse_name = _get_display_name(request_obj.accepted_nurse.user)

        # Notify patient only (nurse completed → no self-notification)
        patient_user = request_obj.get_patient_user()
        if patient_user:
            NotificationService.create_for_object(
                recipient=patient_user,
                title='✔️ Service Completed',
                message=(
                    f'Your {request_obj.service.title} service with {nurse_name} '
                    f'is complete. You can now leave a review.'
                ),
                related_object=request_obj,
                notification_type=NotificationType.NURSE_REQUEST_COMPLETED,
                priority=NotificationPriority.NORMAL,
                action_url=f'/nurse-requests/{request_obj.pk}',
                data={'request_id': str(request_obj.pk)},
            )
            ws_patient = {
                'request': request_data,
                'message': f'Service completed by {nurse_name}',
            }
            cls._ws_to_patient(request_obj, 'nurse_request_completed', ws_patient)

        cls._ws_to_request_group(request_obj, 'nurse_request_completed', {
            'request': request_data,
            'message': 'Service completed',
        })

    @classmethod
    def notify_request_cancelled(cls, request_obj, cancelled_by_user=None, reason: str = ''):
        """
        Notify relevant parties when a request is cancelled.
        """
        request_data = cls._serialize_request(request_obj)
        patient_user = request_obj.get_patient_user()
        patient_name = request_obj.get_patient_display_name()
        reason_text = reason or request_obj.cancellation_reason or 'No reason provided'

        # If the patient cancelled, notify the accepted nurse (if any)
        if cancelled_by_user and patient_user and cancelled_by_user == patient_user:
            if request_obj.accepted_nurse:
                nurse_user = request_obj.accepted_nurse.user
                NotificationService.create_for_object(
                    recipient=nurse_user,
                    title='❌ Request Cancelled',
                    message=(
                        f'{patient_name} cancelled the {request_obj.service.title} '
                        f'request. Reason: {reason_text}'
                    ),
                    related_object=request_obj,
                    notification_type=NotificationType.NURSE_REQUEST_CANCELLED,
                    priority=NotificationPriority.HIGH,
                    action_url=f'/nurse-requests/{request_obj.pk}',
                    data={'request_id': str(request_obj.pk)},
                )
                ws_nurse = {
                    'request': request_data,
                    'cancelled_by': 'patient',
                    'reason': reason_text,
                    'message': f'{patient_name} cancelled the request',
                }
                cls._ws_to_nurse(request_obj.accepted_nurse, 'nurse_request_cancelled', ws_nurse)
        else:
            # Nurse / system cancelled — notify patient
            if patient_user:
                nurse_name = ''
                if request_obj.accepted_nurse:
                    nurse_name = _get_display_name(request_obj.accepted_nurse.user)
                NotificationService.create_for_object(
                    recipient=patient_user,
                    title='❌ Request Cancelled',
                    message=f'Your {request_obj.service.title} request has been cancelled. Reason: {reason_text}',
                    related_object=request_obj,
                    notification_type=NotificationType.NURSE_REQUEST_CANCELLED,
                    priority=NotificationPriority.HIGH,
                    action_url=f'/nurse-requests/{request_obj.pk}',
                    data={'request_id': str(request_obj.pk)},
                )
                ws_patient = {
                    'request': request_data,
                    'cancelled_by': 'nurse' if cancelled_by_user else 'system',
                    'reason': reason_text,
                    'message': 'Your request has been cancelled',
                }
                cls._ws_to_patient(request_obj, 'nurse_request_cancelled', ws_patient)

        # Broadcast to request group
        cls._ws_to_request_group(request_obj, 'nurse_request_cancelled', {
            'request': request_data,
            'reason': reason_text,
            'message': 'Request cancelled',
        })

        # Also broadcast to the city channel so other nurses remove it
        cls._ws_to_city(request_obj.city, 'nurse_request_cancelled', {
            'request_id': request_obj.pk,
            'message': 'Request has been cancelled',
        })
