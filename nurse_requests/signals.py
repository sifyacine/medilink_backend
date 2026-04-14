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
from django.utils import timezone

logger = logging.getLogger(__name__)


def _ensure_patient_record_for_request(request_obj):
    """Resolve or create a patient record for the nurse request patient."""
    from patients.models import PatientRecord

    if request_obj.patient_record:
        return request_obj.patient_record

    user = request_obj.patient_user
    if not user:
        return None

    try:
        return PatientRecord.objects.get(linked_user=user)
    except PatientRecord.DoesNotExist:
        full_name = user.get_full_name().split() if user.get_full_name() else []
        first_name = full_name[0] if full_name else user.email.split('@')[0]
        last_name = full_name[-1] if len(full_name) > 1 else ''
        return PatientRecord.objects.create(
            linked_user=user,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=timezone.now().date(),
            gender='PREFER_NOT_TO_SAY',
            phone_number='',
            email=user.email,
        )


def _grant_medical_access_for_accepted_request(request_obj, nurse_provider):
    """Grant both legacy and current medical record access for accepted nurse requests."""
    if not nurse_provider:
        return

    from patients.models import ProviderPatientAccess
    from medical_record.models import ProviderAccess

    patient_record = _ensure_patient_record_for_request(request_obj)
    if patient_record:
        ProviderPatientAccess.objects.update_or_create(
            provider=nurse_provider,
            patient_record=patient_record,
            defaults={
                'access_level': 'FULL',
                'granted_by': nurse_provider,
            },
        )

    patient_user = request_obj.get_patient_user()
    if patient_user:
        ProviderAccess.objects.update_or_create(
            provider=nurse_provider,
            patient=patient_user,
            defaults={
                'access_type': 'FULL',
                'is_active': True,
                'expires_at': None,
                'reason': f'Auto-granted via nurse request {request_obj.pk}',
            },
        )

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
                    _grant_medical_access_for_accepted_request(fresh, accepted_offer.nurse)
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
