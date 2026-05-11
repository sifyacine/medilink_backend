import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from math import radians, sin, cos, sqrt, atan2
from decimal import Decimal
from .models import (
    NurseServiceRequest,
    NurseOffer,
    RequestHistory,
    RequestStatus,
    OfferStatus
)
from providers.models import Provider, Nurse
from providers.models.nurse import NurseLocation
from common.enums import ProviderStatus

logger = logging.getLogger(__name__)


class NurseRequestService:
    """
    Service class containing business logic for nurse requests.
    Handles state transitions, validations, and related operations.
    """

    @staticmethod
    def create_request(patient_user, validated_data, patient_record=None):
        """
        Create a new nurse service request and set it to SEARCHING status.
        
        Args:
            patient_user: User object for authenticated patient
            validated_data: Validated request data from serializer
            patient_record: Optional PatientRecord for patients without accounts
        """
        with transaction.atomic():
            # Set base_price from service if not provided
            service = validated_data.get('service')
            if service and 'base_price' not in validated_data:
                validated_data['base_price'] = service.price
            
            request = NurseServiceRequest.objects.create(
                patient_user=patient_user,
                patient_record=patient_record,
                **validated_data
            )
            
            # Log creation
            RequestHistory.objects.create(
                request=request,
                actor=patient_user,
                action='REQUEST_CREATED',
                new_status=RequestStatus.CREATED,
                details={'service': request.service.title}
            )
            
            # Transition to SEARCHING
            request.status = RequestStatus.SEARCHING
            request.save()
            
            RequestHistory.objects.create(
                request=request,
                actor=patient_user,
                action='STATUS_CHANGED',
                old_status=RequestStatus.CREATED,
                new_status=RequestStatus.SEARCHING
            )
            
            return request

    @staticmethod
    def _calculate_distance(lat1, lon1, lat2, lon2):
        """
        Calculate distance between two coordinates using Haversine formula.

        Args:
            lat1, lon1: Patient location (Decimal)
            lat2, lon2: Nurse location (Decimal)

        Returns:
            Distance in kilometers (float)
        """
        # Convert Decimal to float
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

        # Convert to radians
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # Earth radius in kilometers
        R = 6371.0
        distance = R * c

        return distance

    @staticmethod
    def get_nurses_within_radius(patient_latitude, patient_longitude, max_distance_km=30):
        """
        Find all available, verified nurses within a radius of patient location.

        Args:
            patient_latitude: Patient location latitude (Decimal)
            patient_longitude: Patient location longitude (Decimal)
            max_distance_km: Maximum distance in kilometers (default: 30)

        Returns:
            List of tuples: [(Nurse object, distance_km), ...]
        """
        # Get all approved, available nurses with their current location
        nurses_with_location = (
            Nurse.objects
            .filter(
                provider__user__is_active=True,
                provider__status=ProviderStatus.APPROVED,
                is_available=True,
            )
            .select_related('provider__user', 'current_location')
        )

        nurses_within_radius = []

        for nurse in nurses_with_location:
            try:
                # Get nurse's current location
                location = nurse.current_location
                if not location or not location.is_active:
                    continue

                # Calculate distance
                distance = NurseRequestService._calculate_distance(
                    patient_latitude,
                    patient_longitude,
                    location.latitude,
                    location.longitude
                )

                # Check if nurse is within service area and max distance
                max_distance_allowed = min(max_distance_km, nurse.service_area_km)

                if distance <= max_distance_allowed:
                    nurses_within_radius.append((nurse, round(distance, 2)))

            except NurseLocation.DoesNotExist:
                # Nurse hasn't submitted location yet
                continue

        # Sort by distance (closest first)
        nurses_within_radius.sort(key=lambda x: x[1])

        return nurses_within_radius

    @staticmethod
    def get_nearby_nurses(request_obj, radius_km=10):
        """
        Find available nurses in the same city.
        In production, this would use geospatial queries.

        DEPRECATED: Use get_nurses_within_radius instead.
        """
        nurses = Provider.objects.filter(
            provider_type='NURSE',
            is_active=True,
            # TODO: Add availability check
            # TODO: Add city/location filtering based on GPS
        )

        # For now, filter by city name
        # In production, use PostGIS or similar for distance calculations
        return nurses

    @staticmethod
    @transaction.atomic
    def nurse_accept_request(request_obj, nurse, **offer_data):
        """
        Nurse accepts the request at the patient's offered price.
        Auto-calculates distance if not provided.
        nurse: Nurse model instance
        """
        # Check if nurse already has an offer (NurseOffer.nurse is FK to Provider)
        existing_offer = NurseOffer.objects.filter(
            request=request_obj,
            nurse=nurse.provider
        ).first()

        if existing_offer:
            raise ValueError("You have already responded to this request")

        # Auto-calculate distance if not provided
        if not offer_data.get('distance_km'):
            try:
                location = nurse.current_location
                if location and location.is_active:
                    distance = NurseRequestService._calculate_distance(
                        request_obj.latitude,
                        request_obj.longitude,
                        location.latitude,
                        location.longitude
                    )
                    offer_data['distance_km'] = round(distance, 2)
            except NurseLocation.DoesNotExist:
                pass  # Location not set, leave distance as None

        # Create offer at patient's price (NurseOffer.nurse is FK to Provider)
        offer = NurseOffer.objects.create(
            request=request_obj,
            nurse=nurse.provider,
            offered_price=request_obj.patient_offered_price,
            status=OfferStatus.PENDING,
            **offer_data
        )

        # Update request status
        if request_obj.status == RequestStatus.SEARCHING:
            request_obj.status = RequestStatus.NURSE_RESPONDED
            request_obj.save()

        # Log action (Nurse.provider.user is the User instance)
        RequestHistory.objects.create(
            request=request_obj,
            actor=nurse.provider.user,
            action='NURSE_ACCEPTED',
            details={
                'nurse_id': nurse.id,
                'nurse_name': f"{nurse.first_name} {nurse.last_name}".strip() or nurse.provider.user.email,
                'offered_price': str(offer.offered_price),
                'distance_km': str(offer.distance_km) if offer.distance_km else 'N/A'
            }
        )

        return offer

    @staticmethod
    @transaction.atomic
    def nurse_counter_offer(request_obj, nurse, offered_price, **offer_data):
        """
        Nurse makes a counter offer with a higher price.
        Auto-calculates distance if not provided.
        nurse: Nurse model instance
        """
        # Check if nurse already has an offer (NurseOffer.nurse is FK to Provider)
        existing_offer = NurseOffer.objects.filter(
            request=request_obj,
            nurse=nurse.provider
        ).first()

        if existing_offer:
            raise ValueError("You have already responded to this request")

        # Auto-calculate distance if not provided
        if not offer_data.get('distance_km'):
            try:
                location = nurse.current_location
                if location and location.is_active:
                    distance = NurseRequestService._calculate_distance(
                        request_obj.latitude,
                        request_obj.longitude,
                        location.latitude,
                        location.longitude
                    )
                    offer_data['distance_km'] = round(distance, 2)
            except NurseLocation.DoesNotExist:
                pass  # Location not set, leave distance as None

        # Create counter offer (NurseOffer.nurse is FK to Provider)
        offer = NurseOffer.objects.create(
            request=request_obj,
            nurse=nurse.provider,
            offered_price=offered_price,
            status=OfferStatus.COUNTER_OFFERED,
            **offer_data
        )

        # Update request status
        if request_obj.status == RequestStatus.SEARCHING:
            request_obj.status = RequestStatus.NURSE_RESPONDED
            request_obj.save()

        # Log action (Nurse.provider.user is the User instance)
        RequestHistory.objects.create(
            request=request_obj,
            actor=nurse.provider.user,
            action='NURSE_COUNTER_OFFERED',
            details={
                'nurse_id': nurse.id,
                'nurse_name': f"{nurse.first_name} {nurse.last_name}".strip() or nurse.provider.user.email,
                'offered_price': str(offer.offered_price),
                'patient_price': str(request_obj.patient_offered_price),
                'distance_km': str(offer.distance_km) if offer.distance_km else 'N/A'
            }
        )

        return offer

    @staticmethod
    @transaction.atomic
    def nurse_reject_request(request_obj, nurse, reason=''):
        """
        Nurse rejects the request without making an offer.
        Creates a REJECTED NurseOffer so the request is excluded from the
        nurse's available list on subsequent fetches (via the
        .exclude(offers__nurse=nurse.provider) filter in get_queryset).
        """
        # Only create the rejected-offer record if no offer exists yet.
        # If the nurse already responded (PENDING/COUNTER_OFFERED), they cannot
        # flip to rejected — that path is blocked at the view level.
        existing = NurseOffer.objects.filter(
            request=request_obj,
            nurse=nurse.provider
        ).first()

        if not existing:
            NurseOffer.objects.create(
                request=request_obj,
                nurse=nurse.provider,
                offered_price=request_obj.patient_offered_price,  # placeholder price
                status=OfferStatus.REJECTED,
            )

        RequestHistory.objects.create(
            request=request_obj,
            actor=nurse.provider.user,
            action='NURSE_REJECTED',
            details={
                'nurse_id': nurse.id,
                'nurse_name': f"{nurse.first_name} {nurse.last_name}".strip() or nurse.provider.user.email,
                'reason': reason
            }
        )

    @staticmethod
    @transaction.atomic
    def patient_accept_offer(request_obj, offer_id):
        """
        Patient accepts a specific nurse offer.
        Returns the updated request object.
        """
        try:
            offer = NurseOffer.objects.get(id=offer_id, request=request_obj)
        except NurseOffer.DoesNotExist:
            raise ValueError("Invalid offer")

        if offer.status not in (OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED):
            raise ValueError("This offer is no longer available")

        # Capture old status BEFORE any mutation
        old_status = request_obj.status

        # Accept the chosen offer
        offer.status = OfferStatus.ACCEPTED
        offer.save()

        # Finalise the request
        request_obj.accepted_nurse = offer.nurse
        request_obj.final_price = offer.offered_price
        request_obj.status = RequestStatus.ACCEPTED
        request_obj.accepted_at = timezone.now()
        request_obj.save()

        # Expire all other pending/counter offers atomically
        NurseOffer.objects.filter(
            request=request_obj
        ).exclude(
            id=offer.id
        ).filter(
            status__in=[OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED]
        ).update(status=OfferStatus.REJECTED)

        RequestHistory.objects.create(
            request=request_obj,
            actor=request_obj.get_patient_user(),
            action='OFFER_ACCEPTED',
            old_status=old_status,
            new_status=RequestStatus.ACCEPTED,
            details={
                'nurse_id': offer.nurse.id,
                'nurse_name': (
                    f"{offer.nurse.user.first_name} {offer.nurse.user.last_name}".strip()
                    or offer.nurse.user.email
                ),
                'final_price': str(request_obj.final_price),
            }
        )

        return request_obj

    @staticmethod
    @transaction.atomic
    def cancel_request(request_obj, reason=''):
        """
        Cancel a request.
        """
        if request_obj.status in [RequestStatus.COMPLETED, RequestStatus.CANCELLED]:
            raise ValueError("This request cannot be cancelled")
        
        old_status = request_obj.status
        request_obj.status = RequestStatus.CANCELLED
        request_obj.cancelled_at = timezone.now()
        request_obj.cancellation_reason = reason
        request_obj.save()
        
        # Reject all pending offers
        NurseOffer.objects.filter(
            request=request_obj,
            status__in=[OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED]
        ).update(status=OfferStatus.EXPIRED)
        
        # Log action
        RequestHistory.objects.create(
            request=request_obj,
            actor=request_obj.get_patient_user(),
            action='REQUEST_CANCELLED',
            old_status=old_status,
            new_status=RequestStatus.CANCELLED,
            details={'reason': reason}
        )
        
        return request_obj

    @staticmethod
    @transaction.atomic
    def start_service(request_obj):
        """
        Mark service as started.
        """
        if request_obj.status != RequestStatus.ACCEPTED:
            raise ValueError("Service can only be started after acceptance")
        
        request_obj.status = RequestStatus.IN_PROGRESS
        request_obj.started_at = timezone.now()
        request_obj.save()
        
        RequestHistory.objects.create(
            request=request_obj,
            actor=request_obj.accepted_nurse.user,
            action='SERVICE_STARTED',
            old_status=RequestStatus.ACCEPTED,
            new_status=RequestStatus.IN_PROGRESS
        )
        
        return request_obj

    @staticmethod
    @transaction.atomic
    def complete_service(request_obj):
        """
        Mark service as completed.
        """
        if request_obj.status != RequestStatus.IN_PROGRESS:
            raise ValueError("Service must be in progress to complete")

        request_obj.status = RequestStatus.COMPLETED
        request_obj.completed_at = timezone.now()
        request_obj.save()

        RequestHistory.objects.create(
            request=request_obj,
            actor=request_obj.accepted_nurse.user,
            action='SERVICE_COMPLETED',
            old_status=RequestStatus.IN_PROGRESS,
            new_status=RequestStatus.COMPLETED
        )

        return request_obj

    # ------------------------------------------------------------------
    # Auto-transition (called by management command every minute)
    # ------------------------------------------------------------------

    @classmethod
    def run_auto_transitions(cls):
        """
        Scan open requests and apply time-based status transitions.

        Called by `manage.py auto_transition_nurse_requests` (run via cron
        every minute — no Celery required).

        Returns a dict with counts for each transition type performed.
        """
        cfg = settings.MEDILINK.get('NURSE_REQUEST_TIMEOUTS', {})
        searching_timeout   = cfg.get('SEARCHING_TIMEOUT_MINUTES', 30)
        decision_timeout    = cfg.get('OFFER_DECISION_TIMEOUT_MINUTES', 15)
        start_timeout_hours = cfg.get('START_TIMEOUT_HOURS', 2)
        completion_buffer   = cfg.get('COMPLETION_BUFFER_MINUTES', 30)
        offer_expiry        = cfg.get('OFFER_EXPIRY_MINUTES', 20)

        now = timezone.now()
        counts = {
            'searching_cancelled': 0,
            'offers_expired':      0,
            'decision_cancelled':  0,
            'start_cancelled':     0,
            'in_progress_completed': 0,
        }

        # 1. SEARCHING → CANCELLED (no offers within timeout)
        cutoff = now - timedelta(minutes=searching_timeout)
        stale_searching = NurseServiceRequest.objects.filter(
            status=RequestStatus.SEARCHING,
            updated_at__lte=cutoff,
        ).select_related('service')
        for req in stale_searching:
            try:
                cls._auto_cancel(
                    req,
                    reason='No nurses were available in your area. Please try again.',
                    action='AUTO_CANCELLED_NO_RESPONSE',
                )
                counts['searching_cancelled'] += 1
            except Exception as exc:
                logger.error('Auto-cancel SEARCHING failed for request %s: %s', req.pk, exc)

        # 2. Expire individual PENDING / COUNTER_OFFERED offers past their window
        offer_cutoff = now - timedelta(minutes=offer_expiry)
        expired_count = NurseOffer.objects.filter(
            status__in=[OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED],
            created_at__lte=offer_cutoff,
        ).update(status=OfferStatus.EXPIRED)
        counts['offers_expired'] = expired_count

        # 3. NURSE_RESPONDED → CANCELLED (patient took too long to decide)
        #    Only trigger when ALL remaining offers are now expired/rejected.
        decision_cutoff = now - timedelta(minutes=decision_timeout)
        responded_reqs = NurseServiceRequest.objects.filter(
            status=RequestStatus.NURSE_RESPONDED,
            updated_at__lte=decision_cutoff,
        ).prefetch_related('offers')
        for req in responded_reqs:
            has_live_offer = req.offers.filter(
                status__in=[OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED]
            ).exists()
            if not has_live_offer:
                try:
                    cls._auto_cancel(
                        req,
                        reason='All nurse offers have expired. Please create a new request.',
                        action='AUTO_CANCELLED_OFFERS_EXPIRED',
                    )
                    counts['decision_cancelled'] += 1
                except Exception as exc:
                    logger.error('Auto-cancel NURSE_RESPONDED failed for request %s: %s', req.pk, exc)

        # 4. ACCEPTED → CANCELLED (nurse never arrived / started within timeout)
        start_cutoff = now - timedelta(hours=start_timeout_hours)
        unstarted = NurseServiceRequest.objects.filter(
            status=RequestStatus.ACCEPTED,
            accepted_at__lte=start_cutoff,
        ).select_related('accepted_nurse__user', 'service')
        for req in unstarted:
            try:
                cls._auto_cancel(
                    req,
                    reason='The nurse did not start the service in time. Please create a new request.',
                    action='AUTO_CANCELLED_NURSE_NO_SHOW',
                )
                counts['start_cancelled'] += 1
            except Exception as exc:
                logger.error('Auto-cancel ACCEPTED failed for request %s: %s', req.pk, exc)

        # 5. IN_PROGRESS → COMPLETED (service duration + buffer elapsed)
        in_progress = NurseServiceRequest.objects.filter(
            status=RequestStatus.IN_PROGRESS,
            started_at__isnull=False,
        ).select_related('service', 'accepted_nurse__user')
        for req in in_progress:
            duration_minutes = getattr(req.service, 'duration_minutes', None) or 60
            expected_end = req.started_at + timedelta(
                minutes=duration_minutes + completion_buffer
            )
            if now >= expected_end:
                try:
                    with transaction.atomic():
                        req.status = RequestStatus.COMPLETED
                        req.completed_at = now
                        req.save(update_fields=['status', 'completed_at', 'updated_at'])
                        RequestHistory.objects.create(
                            request=req,
                            actor=None,
                            action='AUTO_COMPLETED',
                            old_status=RequestStatus.IN_PROGRESS,
                            new_status=RequestStatus.COMPLETED,
                            details={
                                'reason': 'Auto-completed: service duration elapsed',
                                'duration_minutes': duration_minutes,
                                'buffer_minutes': completion_buffer,
                            },
                        )
                    cls._fire_status_changed(req, RequestStatus.IN_PROGRESS, RequestStatus.COMPLETED)
                    counts['in_progress_completed'] += 1
                except Exception as exc:
                    logger.error('Auto-complete IN_PROGRESS failed for request %s: %s', req.pk, exc)

        return counts

    @classmethod
    def _auto_cancel(cls, req, reason: str, action: str):
        """Atomically cancel a request and fire the status-changed signal."""
        old_status = req.status
        with transaction.atomic():
            # Expire any live offers
            NurseOffer.objects.filter(
                request=req,
                status__in=[OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED],
            ).update(status=OfferStatus.EXPIRED)

            req.status = RequestStatus.CANCELLED
            req.cancelled_at = timezone.now()
            req.cancellation_reason = reason
            req.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'updated_at'])

            RequestHistory.objects.create(
                request=req,
                actor=None,
                action=action,
                old_status=old_status,
                new_status=RequestStatus.CANCELLED,
                details={'reason': reason, 'auto': True},
            )
        cls._fire_status_changed(req, old_status, RequestStatus.CANCELLED)

    @staticmethod
    def _fire_status_changed(req, old_status: str, new_status: str):
        """Dispatch the request_status_changed signal (notifications run on_commit)."""
        from .signals import request_status_changed
        request_status_changed.send(
            sender=NurseRequestService,
            request=req,
            old_status=old_status,
            new_status=new_status,
        )
