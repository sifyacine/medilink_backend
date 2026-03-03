"""
Signals for the nurse_requests app.

These Django signals are emitted by views / service methods and handled
here to fire real-time notifications (WebSocket + FCM + in-app) via
``NurseRequestNotifier``.

All notification work runs inside ``transaction.on_commit`` so that listeners
only see committed data.
"""
import logging
import django.dispatch
from django.db import transaction

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Custom signals (dispatched from views)
# -----------------------------------------------------------------------

# Sent when a patient creates a new request
request_created = django.dispatch.Signal()        # kwargs: request

# Sent when the request status changes
request_status_changed = django.dispatch.Signal()  # kwargs: request, old_status, new_status

# Sent when a nurse submits an offer (accept or counter-offer)
nurse_offer_submitted = django.dispatch.Signal()   # kwargs: request, offer


# -----------------------------------------------------------------------
# Receivers
# -----------------------------------------------------------------------

def _on_request_created(sender, request, **kwargs):
    """Handle new nurse request creation."""
    from .notifications import NurseRequestNotifier
    from .models import NurseServiceRequest

    request_id = request.pk

    def _notify():
        try:
            fresh = NurseServiceRequest.objects.select_related(
                'service', 'patient_user', 'patient_record',
                'accepted_nurse__user', 'address',
            ).prefetch_related('offers__nurse__user').get(pk=request_id)
            NurseRequestNotifier.notify_new_request(fresh)
        except NurseServiceRequest.DoesNotExist:
            logger.warning("NurseServiceRequest %s gone before notification", request_id)
        except Exception as e:
            logger.error("Error notifying new nurse request: %s", e)

    transaction.on_commit(_notify)


def _on_status_changed(sender, request, old_status, new_status, **kwargs):
    """Handle request status transitions."""
    from .notifications import NurseRequestNotifier
    from .models import NurseServiceRequest, RequestStatus

    request_id = request.pk

    def _notify():
        try:
            fresh = NurseServiceRequest.objects.select_related(
                'service', 'patient_user', 'patient_record',
                'accepted_nurse__user', 'address',
            ).prefetch_related('offers__nurse__user').get(pk=request_id)

            if new_status == RequestStatus.ACCEPTED:
                accepted_offer = fresh.offers.filter(status='ACCEPTED').select_related('nurse__user').first()
                if accepted_offer:
                    NurseRequestNotifier.notify_offer_accepted(fresh, accepted_offer)

            elif new_status == RequestStatus.IN_PROGRESS:
                NurseRequestNotifier.notify_service_started(fresh)

            elif new_status == RequestStatus.COMPLETED:
                NurseRequestNotifier.notify_service_completed(fresh)

            elif new_status == RequestStatus.CANCELLED:
                cancelled_by = fresh.get_patient_user()  # default to patient
                NurseRequestNotifier.notify_request_cancelled(
                    fresh,
                    cancelled_by_user=cancelled_by,
                    reason=fresh.cancellation_reason,
                )
        except NurseServiceRequest.DoesNotExist:
            logger.warning("NurseServiceRequest %s gone before notification", request_id)
        except Exception as e:
            logger.error("Error notifying nurse request status change: %s", e)

    transaction.on_commit(_notify)


def _on_offer_submitted(sender, request, offer, **kwargs):
    """Handle nurse offer/counter-offer."""
    from .notifications import NurseRequestNotifier
    from .models import NurseServiceRequest, NurseOffer

    request_id = request.pk
    offer_id = offer.pk

    def _notify():
        try:
            fresh_request = NurseServiceRequest.objects.select_related(
                'service', 'patient_user', 'patient_record',
                'accepted_nurse__user', 'address',
            ).prefetch_related('offers__nurse__user').get(pk=request_id)
            fresh_offer = NurseOffer.objects.select_related('nurse__user').get(pk=offer_id)
            NurseRequestNotifier.notify_nurse_offer(fresh_request, fresh_offer)
        except (NurseServiceRequest.DoesNotExist, NurseOffer.DoesNotExist):
            logger.warning("Request/Offer gone before notification")
        except Exception as e:
            logger.error("Error notifying nurse offer: %s", e)

    transaction.on_commit(_notify)


# Connect receivers
request_created.connect(_on_request_created)
request_status_changed.connect(_on_status_changed)
nurse_offer_submitted.connect(_on_offer_submitted)
