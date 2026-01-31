from django.db import transaction
from django.utils import timezone
from .models import (
    NurseServiceRequest,
    NurseOffer,
    RequestHistory,
    RequestStatus,
    OfferStatus
)
from providers.models import Provider


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
    def get_nearby_nurses(request_obj, radius_km=10):
        """
        Find available nurses in the same city.
        In production, this would use geospatial queries.
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
        """
        # Check if nurse already has an offer
        existing_offer = NurseOffer.objects.filter(
            request=request_obj,
            nurse=nurse
        ).first()
        
        if existing_offer:
            raise ValueError("You have already responded to this request")
        
        # Create offer at patient's price
        offer = NurseOffer.objects.create(
            request=request_obj,
            nurse=nurse,
            offered_price=request_obj.patient_offered_price,
            status=OfferStatus.PENDING,
            **offer_data
        )
        
        # Update request status
        if request_obj.status == RequestStatus.SEARCHING:
            request_obj.status = RequestStatus.NURSE_RESPONDED
            request_obj.save()
        
        # Log action
        RequestHistory.objects.create(
            request=request_obj,
            actor=nurse.user,
            action='NURSE_ACCEPTED',
            details={
                'nurse_id': nurse.id,
                'nurse_name': f"{nurse.user.first_name} {nurse.user.last_name}",
                'offered_price': str(offer.offered_price)
            }
        )
        
        return offer

    @staticmethod
    @transaction.atomic
    def nurse_counter_offer(request_obj, nurse, offered_price, **offer_data):
        """
        Nurse makes a counter offer with a higher price.
        """
        # Check if nurse already has an offer
        existing_offer = NurseOffer.objects.filter(
            request=request_obj,
            nurse=nurse
        ).first()
        
        if existing_offer:
            raise ValueError("You have already responded to this request")
        
        # Create counter offer
        offer = NurseOffer.objects.create(
            request=request_obj,
            nurse=nurse,
            offered_price=offered_price,
            status=OfferStatus.COUNTER_OFFERED,
            **offer_data
        )
        
        # Update request status
        if request_obj.status == RequestStatus.SEARCHING:
            request_obj.status = RequestStatus.NURSE_RESPONDED
            request_obj.save()
        
        # Log action
        RequestHistory.objects.create(
            request=request_obj,
            actor=nurse.user,
            action='NURSE_COUNTER_OFFERED',
            details={
                'nurse_id': nurse.id,
                'nurse_name': f"{nurse.user.first_name} {nurse.user.last_name}",
                'offered_price': str(offer.offered_price),
                'patient_price': str(request_obj.patient_offered_price)
            }
        )
        
        return offer

    @staticmethod
    @transaction.atomic
    def nurse_reject_request(request_obj, nurse, reason=''):
        """
        Nurse rejects the request.
        """
        # Log rejection
        RequestHistory.objects.create(
            request=request_obj,
            actor=nurse.user,
            action='NURSE_REJECTED',
            details={
                'nurse_id': nurse.id,
                'nurse_name': f"{nurse.user.first_name} {nurse.user.last_name}",
                'reason': reason
            }
        )

    @staticmethod
    @transaction.atomic
    def patient_accept_offer(request_obj, offer_id):
        """
        Patient accepts a specific nurse offer.
        This finalizes the request.
        """
        try:
            offer = NurseOffer.objects.get(id=offer_id, request=request_obj)
        except NurseOffer.DoesNotExist:
            raise ValueError("Invalid offer")
        
        if offer.status != OfferStatus.PENDING and offer.status != OfferStatus.COUNTER_OFFERED:
            raise ValueError("This offer is no longer available")
        
        # Update offer status
        offer.status = OfferStatus.ACCEPTED
        offer.save()
        
        # Update request
        request_obj.accepted_nurse = offer.nurse
        request_obj.final_price = offer.offered_price
        request_obj.status = RequestStatus.ACCEPTED
        request_obj.accepted_at = timezone.now()
        request_obj.save()
        
        # Reject all other offers
        NurseOffer.objects.filter(
            request=request_obj
        ).exclude(
            id=offer.id
        ).update(
            status=OfferStatus.REJECTED
        )
        
        # Log action
        RequestHistory.objects.create(
            request=request_obj,
            actor=request_obj.get_patient_user(),
            action='OFFER_ACCEPTED',
            old_status=request_obj.status,
            new_status=RequestStatus.ACCEPTED,
            details={
                'nurse_id': offer.nurse.id,
                'nurse_name': f"{offer.nurse.user.first_name} {offer.nurse.user.last_name}",
                'final_price': str(request_obj.final_price)
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
