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
        # Get all active, verified, available nurses with current location
        nurses_with_location = (
            Nurse.objects
            .filter(
                provider__is_active=True,
                is_verified=True,
                is_available=True
            )
            .select_related('provider', 'current_location')
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
        Nurse rejects the request.
        """
        # Log rejection (Nurse.provider.user is the User instance)
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
