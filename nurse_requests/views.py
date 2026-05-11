import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from .models import (
    NurseServiceRequest,
    NurseOffer,
    RequestHistory,
    RequestStatus,
    OfferStatus
)

logger = logging.getLogger(__name__)
from services.models import Service, ServiceType, NurseService
from address.models import Address
from .serializers import (
    NursingServiceSerializer,
    NurseServiceRequestListSerializer,
    NurseServiceRequestDetailSerializer,
    CreateNurseServiceRequestSerializer,
    AcceptOfferSerializer,
    CancelRequestSerializer,
    NurseAvailableRequestSerializer,
    NurseAcceptRequestSerializer,
    NurseCounterOfferSerializer,
    NurseProfileServiceSerializer,
    PatientSavedAddressSerializer,
    NurseProfileDetailSerializer,
    NurseReviewHistorySerializer,
    NurseRequestHistorySerializer,
)
from providers.models import Provider, Nurse
from .permissions import IsPatient, IsNurse, IsRequestOwner
from .services import NurseRequestService
from .signals import request_created, request_status_changed, nurse_offer_submitted
from common.views import StandardPagination


# =============================================================================
# ERROR CODES - Comprehensive error code system for client handling
# =============================================================================

class ErrorCodes:
    """Centralized error codes for the nurse requests system"""
    # Service errors (1xxx)
    SERVICE_NOT_FOUND = 'NR1001'
    SERVICE_INACTIVE = 'NR1002'
    SERVICE_NOT_NURSING = 'NR1003'
    SERVICE_NOT_ON_DEMAND = 'NR1004'
    SERVICE_ALREADY_ADDED = 'NR1005'
    SERVICE_NOT_IN_PROFILE = 'NR1006'
    
    # Price errors (2xxx)
    PRICE_BELOW_BASE = 'NR2001'
    PRICE_BELOW_PATIENT_OFFER = 'NR2002'
    PRICE_INVALID = 'NR2003'
    
    # Request errors (3xxx)
    REQUEST_NOT_FOUND = 'NR3001'
    REQUEST_NOT_OWNER = 'NR3002'
    REQUEST_INVALID_STATUS = 'NR3003'
    REQUEST_ALREADY_CANCELLED = 'NR3004'
    REQUEST_ALREADY_ACCEPTED = 'NR3005'
    REQUEST_ALREADY_COMPLETED = 'NR3006'
    REQUEST_SERVICE_NOT_IN_NURSE_PROFILE = 'NR3007'
    
    # Offer errors (4xxx)
    OFFER_NOT_FOUND = 'NR4001'
    OFFER_NOT_AVAILABLE = 'NR4002'
    OFFER_ALREADY_SUBMITTED = 'NR4003'
    OFFER_EXPIRED = 'NR4004'
    
    # Location errors (5xxx)
    LOCATION_REQUIRED = 'NR5001'
    LOCATION_INVALID_COORDS = 'NR5002'
    CITY_REQUIRED = 'NR5003'
    ADDRESS_NOT_FOUND = 'NR5004'
    
    # Auth/Permission errors (6xxx)
    NOT_AUTHENTICATED = 'NR6001'
    NOT_PATIENT = 'NR6002'
    NOT_NURSE = 'NR6003'
    NURSE_PROFILE_NOT_FOUND = 'NR6004'
    NURSE_NOT_VERIFIED = 'NR6005'


def error_response(code, message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """Standard error response format"""
    response_data = {
        'success': False,
        'error': {
            'code': code,
            'message': message,
        }
    }
    if details:
        response_data['error']['details'] = details
    return Response(response_data, status=status_code)


# =============================================================================
# PUBLIC NURSING SERVICES CATALOG
# =============================================================================

class NursingServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing available nursing services.
    Patients use this to see what services they can request.
    Only shows services with service_type='NURSE' and is_on_demand=True.
    
    GET /api/nurse-requests/services/ - List all nursing services
    GET /api/nurse-requests/services/{id}/ - Get service details
    """
    serializer_class = NursingServiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only active nursing services available for on-demand requests"""
        return Service.objects.filter(
            is_active=True,
            service_type=ServiceType.NURSE,
            is_on_demand=True
        )
    
    def list(self, request, *args, **kwargs):
        """List services with additional metadata"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'results': serializer.data,
            'message': 'Select a service to request a nurse'
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get service details with nurse availability info"""
        try:
            instance = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.SERVICE_NOT_FOUND,
                'Nursing service not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        
        # Count available nurses for this service
        # Note: is_verified is a property, not a field. Use status='APPROVED' instead.
        available_nurses_count = NurseService.objects.filter(
            service=instance,
            is_available=True,
            nurse__provider__status='APPROVED'
        ).count()
        
        return Response({
            'success': True,
            'data': serializer.data,
            'available_nurses_count': available_nurses_count,
            'message': f'{available_nurses_count} nurses available for this service'
        })


# =============================================================================
# PATIENT ENDPOINTS
# =============================================================================

class PatientNurseRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for patients to manage their nurse service requests.

    Endpoints:
    - GET /patient/nurse-requests/ - List all my requests
    - POST /patient/nurse-requests/ - Create new request
    - GET /patient/nurse-requests/{id}/ - Get request details
    - POST /patient/nurse-requests/{id}/accept/ - Accept a nurse offer
    - POST /patient/nurse-requests/{id}/cancel/ - Cancel request
    """
    permission_classes = [IsAuthenticated, IsPatient]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """
        Return all the current patient's requests (full history).
        
        Query Parameters:
        - status: Filter by specific status (e.g., COMPLETED, CANCELLED, SEARCHING)
        - is_active: Filter active requests (SEARCHING, NURSE_RESPONDED, PATIENT_DECISION, ACCEPTED, IN_PROGRESS)
        - is_history: Filter historical requests (COMPLETED, CANCELLED)
        """
        queryset = NurseServiceRequest.objects.filter(
            Q(patient_user=self.request.user) |
            Q(patient_record__linked_user=self.request.user)
        ).select_related(
            'service', 'patient_user', 'patient_record', 'accepted_nurse__user'
        ).prefetch_related(
            'offers__nurse__user'
        ).order_by('-created_at')
        
        # Filter by specific status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        
        # Filter active vs historical
        is_active = self.request.query_params.get('is_active')
        is_history = self.request.query_params.get('is_history')
        
        active_statuses = [
            RequestStatus.CREATED, RequestStatus.SEARCHING, 
            RequestStatus.NURSE_RESPONDED, RequestStatus.PATIENT_DECISION,
            RequestStatus.ACCEPTED, RequestStatus.IN_PROGRESS
        ]
        history_statuses = [RequestStatus.COMPLETED, RequestStatus.CANCELLED]
        
        if is_active and is_active.lower() == 'true':
            queryset = queryset.filter(status__in=active_statuses)
        elif is_history and is_history.lower() == 'true':
            queryset = queryset.filter(status__in=history_statuses)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return NurseServiceRequestListSerializer
        elif self.action == 'create':
            return CreateNurseServiceRequestSerializer
        return NurseServiceRequestDetailSerializer
    
    def perform_create(self, serializer):
        """Create request and broadcast to nurses"""
        # Patient user is the current authenticated user
        request_obj = NurseRequestService.create_request(
            patient_user=self.request.user,
            validated_data=serializer.validated_data
        )
        
        # Send signal for real-time broadcasting
        request_created.send(
            sender=self.__class__,
            request=request_obj
        )
        
        return request_obj
    
    def create(self, request, *args, **kwargs):
        """Override to return detailed serializer in response"""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            # Parse validation errors and return with error codes
            errors = serializer.errors
            error_details = []
            
            for field, messages in errors.items():
                if field == 'service':
                    if 'does not exist' in str(messages):
                        return error_response(
                            ErrorCodes.SERVICE_NOT_FOUND,
                            'The selected nursing service does not exist',
                            {'field': field, 'messages': messages}
                        )
                    elif 'not a nursing service' in str(messages):
                        return error_response(
                            ErrorCodes.SERVICE_NOT_NURSING,
                            'The selected service is not a nursing service',
                            {'field': field, 'messages': messages}
                        )
                    elif 'not available for on-demand' in str(messages):
                        return error_response(
                            ErrorCodes.SERVICE_NOT_ON_DEMAND,
                            'This service is not available for on-demand requests',
                            {'field': field, 'messages': messages}
                        )
                elif field == 'patient_offered_price':
                    return error_response(
                        ErrorCodes.PRICE_BELOW_BASE,
                        'Your offered price must be at least the base price',
                        {'field': field, 'messages': messages}
                    )
                elif field in ['latitude', 'longitude']:
                    return error_response(
                        ErrorCodes.LOCATION_INVALID_COORDS,
                        'Invalid location coordinates provided',
                        {'field': field, 'messages': messages}
                    )
                elif field == 'city':
                    return error_response(
                        ErrorCodes.CITY_REQUIRED,
                        'City is required for the service location',
                        {'field': field, 'messages': messages}
                    )
                
                error_details.append({'field': field, 'messages': messages})
            
            return error_response(
                'NR0001',
                'Validation failed',
                error_details
            )
        
        request_obj = self.perform_create(serializer)
        
        # Return detailed response
        response_serializer = NurseServiceRequestDetailSerializer(request_obj)
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Request created successfully. Searching for available nurses...'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='saved-addresses')
    def saved_addresses(self, request):
        """
        Get patient's saved addresses for quick selection.
        
        Returns addresses associated with the current user that can be used
        for the nurse service request location.
        """
        user = request.user
        content_type = ContentType.objects.get_for_model(user)
        
        addresses = Address.objects.filter(
            content_type=content_type,
            object_id=user.id
        ).order_by('-is_primary', '-updated_at')
        
        serializer = PatientSavedAddressSerializer(addresses, many=True)
        
        return Response({
            'success': True,
            'count': addresses.count(),
            'results': serializer.data,
            'message': 'Select a saved address or choose location from map'
        })
    
    @action(detail=False, methods=['post'], url_path='use-saved-address')
    def use_saved_address(self, request):
        """
        Create a nurse request using a saved address.
        
        Body:
        {
            "service": 1,
            "patient_offered_price": "75.00",
            "address_id": 5,
            "notes": "Optional notes"
        }
        """
        address_id = request.data.get('address_id')
        
        if not address_id:
            return error_response(
                ErrorCodes.ADDRESS_NOT_FOUND,
                'address_id is required'
            )
        
        # Get the address
        user = request.user
        content_type = ContentType.objects.get_for_model(user)
        
        try:
            address = Address.objects.get(
                id=address_id,
                content_type=content_type,
                object_id=user.id
            )
        except Address.DoesNotExist:
            return error_response(
                ErrorCodes.ADDRESS_NOT_FOUND,
                'Address not found or does not belong to you',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validate coordinates
        if not address.latitude or not address.longitude:
            return error_response(
                ErrorCodes.LOCATION_INVALID_COORDS,
                'This address does not have valid coordinates. Please select location from map.',
                {'address_id': address_id}
            )
        
        # Build request data with address info
        request_data = {
            'service': request.data.get('service'),
            'patient_offered_price': request.data.get('patient_offered_price'),
            'latitude': str(address.latitude),
            'longitude': str(address.longitude),
            'city': address.city or 'Unknown',
            'address_line': str(address),
            'notes': request.data.get('notes', '')
        }
        
        # Use the create serializer
        serializer = CreateNurseServiceRequestSerializer(data=request_data)
        
        if not serializer.is_valid():
            return error_response(
                'NR0001',
                'Validation failed',
                serializer.errors
            )
        
        request_obj = NurseRequestService.create_request(
            patient_user=self.request.user,
            validated_data=serializer.validated_data
        )
        
        request_created.send(sender=self.__class__, request=request_obj)
        
        response_serializer = NurseServiceRequestDetailSerializer(request_obj)
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Request created successfully using your saved address'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept a nurse offer.
        
        Body:
        {
            "offer_id": 123
        }
        """
        try:
            request_obj = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validate permissions (already filtered by get_queryset)
        if request_obj.patient_user != request.user:
            return error_response(
                ErrorCodes.REQUEST_NOT_OWNER,
                'You do not have permission to accept offers on this request',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Validate status
        if request_obj.status == RequestStatus.CANCELLED:
            return error_response(
                ErrorCodes.REQUEST_ALREADY_CANCELLED,
                'This request has been cancelled'
            )
        
        if request_obj.status == RequestStatus.ACCEPTED:
            return error_response(
                ErrorCodes.REQUEST_ALREADY_ACCEPTED,
                'This request already has an accepted offer'
            )
        
        if request_obj.status == RequestStatus.COMPLETED:
            return error_response(
                ErrorCodes.REQUEST_ALREADY_COMPLETED,
                'This request has already been completed'
            )
        
        if request_obj.status not in [
            RequestStatus.NURSE_RESPONDED,
            RequestStatus.PATIENT_DECISION
        ]:
            return error_response(
                ErrorCodes.REQUEST_INVALID_STATUS,
                'Cannot accept offers at this stage. Wait for nurses to respond.',
                {'current_status': request_obj.status}
            )
        
        serializer = AcceptOfferSerializer(
            data=request.data,
            context={'request_obj': request_obj}
        )
        
        if not serializer.is_valid():
            return error_response(
                ErrorCodes.OFFER_NOT_FOUND,
                'Invalid offer selected',
                serializer.errors
            )
        
        # Capture before the service mutates the object
        old_status = request_obj.status

        try:
            updated_request = NurseRequestService.patient_accept_offer(
                request_obj=request_obj,
                offer_id=serializer.validated_data['offer_id']
            )

            request_status_changed.send(
                sender=self.__class__,
                request=updated_request,
                old_status=old_status,
                new_status=updated_request.status,
            )

            response_serializer = NurseServiceRequestDetailSerializer(updated_request)
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Offer accepted! The nurse will be on their way.',
            })
        except ValueError as e:
            return error_response(
                ErrorCodes.OFFER_NOT_AVAILABLE,
                str(e)
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a request.
        
        Body:
        {
            "cancellation_reason": "Changed my mind"
        }
        """
        try:
            request_obj = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validate permissions
        if request_obj.patient_user != request.user:
            return error_response(
                ErrorCodes.REQUEST_NOT_OWNER,
                'You do not have permission to cancel this request',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already cancelled
        if request_obj.status == RequestStatus.CANCELLED:
            return error_response(
                ErrorCodes.REQUEST_ALREADY_CANCELLED,
                'This request has already been cancelled'
            )
        
        # Check if already completed
        if request_obj.status == RequestStatus.COMPLETED:
            return error_response(
                ErrorCodes.REQUEST_ALREADY_COMPLETED,
                'Cannot cancel a completed request'
            )
        
        serializer = CancelRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Capture before the service mutates the object
        old_status = request_obj.status

        try:
            updated_request = NurseRequestService.cancel_request(
                request_obj=request_obj,
                reason=serializer.validated_data.get('cancellation_reason', '')
            )

            request_status_changed.send(
                sender=self.__class__,
                request=updated_request,
                old_status=old_status,
                new_status=RequestStatus.CANCELLED,
            )

            response_serializer = NurseServiceRequestDetailSerializer(updated_request)
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Request cancelled successfully',
            })
        except ValueError as e:
            return error_response(
                ErrorCodes.REQUEST_INVALID_STATUS,
                str(e)
            )
    
    @action(detail=True, methods=['post'])
    def decline_offer(self, request, pk=None):
        """
        Decline a specific nurse offer without cancelling the entire request.
        Patient can continue reviewing other offers.

        Body:
        {
            "offer_id": 123,
            "reason": "Looking for other options"  # Optional
        }
        """
        try:
            request_obj = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validate permissions
        if request_obj.patient_user != request.user:
            return error_response(
                ErrorCodes.REQUEST_NOT_OWNER,
                'You do not have permission to decline offers on this request',
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Validate status - can only decline when there are pending offers
        if request_obj.status == RequestStatus.ACCEPTED:
            return error_response(
                ErrorCodes.REQUEST_ALREADY_ACCEPTED,
                'This request already has an accepted offer'
            )

        if request_obj.status == RequestStatus.CANCELLED:
            return error_response(
                ErrorCodes.REQUEST_ALREADY_CANCELLED,
                'This request has been cancelled'
            )

        if request_obj.status == RequestStatus.COMPLETED:
            return error_response(
                ErrorCodes.REQUEST_ALREADY_COMPLETED,
                'This request has already been completed'
            )

        # Get offer to decline
        offer_id = request.data.get('offer_id')
        reason = request.data.get('reason', '')

        if not offer_id:
            return error_response(
                ErrorCodes.OFFER_NOT_FOUND,
                'offer_id is required',
                {'field': 'offer_id'}
            )

        try:
            offer = NurseOffer.objects.get(id=offer_id, request=request_obj)
        except NurseOffer.DoesNotExist:
            return error_response(
                ErrorCodes.OFFER_NOT_FOUND,
                'Invalid offer selected',
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if offer is still pending
        if offer.status not in [OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED]:
            return error_response(
                ErrorCodes.OFFER_NOT_AVAILABLE,
                'This offer is no longer available for declining'
            )

        # Decline the offer
        old_status = offer.status
        offer.status = OfferStatus.REJECTED
        offer.save()

        # Log to request history
        RequestHistory.objects.create(
            request=request_obj,
            actor=request.user,
            action='OFFER_DECLINED',
            details={
                'offer_id': offer.id,
                'nurse_id': offer.nurse.id,
                'nurse_name': offer.nurse.user.get_full_name() or offer.nurse.user.email,
                'declined_price': f"{float(offer.offered_price):.2f} DZD",
                'reason': reason
            }
        )

        # Notify the nurse that their offer was declined
        try:
            from .notifications import NurseRequestNotifier
            NurseRequestNotifier.notify_offer_declined(request_obj, offer.nurse, reason)
        except Exception as e:
            logger.error("Failed to send decline notification: %s", e)

        response_serializer = NurseServiceRequestDetailSerializer(request_obj)
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': f'Offer declined. You can continue reviewing other offers.'
        })

    @action(detail=True, methods=['get'], url_path='nurse-profile/(?P<nurse_id>[^/.]+)')
    def nurse_profile(self, request, pk=None, nurse_id=None):
        """
        Get detailed profile of a nurse who made an offer.
        Allows patients to review nurse credentials before accepting.

        GET /patient/nurse-requests/{request_id}/nurse-profile/{nurse_id}/
        """
        try:
            request_obj = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verify the nurse has made an offer on this request
        try:
            offer = NurseOffer.objects.get(
                request=request_obj,
                nurse_id=nurse_id
            )
        except NurseOffer.DoesNotExist:
            return error_response(
                ErrorCodes.OFFER_NOT_FOUND,
                'This nurse has not made an offer on this request',
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Get the nurse profile
        try:
            nurse = Nurse.objects.get(provider_id=nurse_id)
        except Nurse.DoesNotExist:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = NurseProfileDetailSerializer(nurse, context={'request': request})
        
        return Response({
            'success': True,
            'data': serializer.data,
            'offer': {
                'id': offer.id,
                'offered_price': str(offer.offered_price),
                'status': offer.status,
                'estimated_arrival_time': str(offer.estimated_arrival_time) if offer.estimated_arrival_time else None,
                'notes': offer.notes,
            },
            'message': 'Nurse profile retrieved successfully'
        })
    
    @action(detail=True, methods=['get'], url_path='nurse-history/(?P<nurse_id>[^/.]+)')
    def nurse_history(self, request, pk=None, nurse_id=None):
        """
        Get a nurse's completed service history.
        Shows recent completed services with anonymized patient info.
        
        GET /patient/nurse-requests/{request_id}/nurse-history/{nurse_id}/
        """
        try:
            request_obj = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Verify the nurse has made an offer
        if not NurseOffer.objects.filter(
            request=request_obj,
            nurse_id=nurse_id
        ).exists():
            return error_response(
                ErrorCodes.OFFER_NOT_FOUND,
                'This nurse has not made an offer on this request',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get completed services for this nurse
        completed_services = NurseServiceRequest.objects.filter(
            accepted_nurse_id=nurse_id,
            status=RequestStatus.COMPLETED
        ).select_related('service').order_by('-completed_at')[:10]
        
        serializer = NurseReviewHistorySerializer(
            completed_services,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'count': completed_services.count(),
            'results': serializer.data,
            'message': 'Nurse service history retrieved'
        })


# =============================================================================
# NURSE PROFILE SERVICES MANAGEMENT
# =============================================================================

class NurseProfileServicesViewSet(viewsets.ViewSet):
    """
    ViewSet for nurses to manage their profile services.
    Nurses must add services to their profile to receive on-demand requests.
    
    Endpoints:
    - GET /nurse/my-services/ - List my nursing services
    - POST /nurse/my-services/add/ - Add a nursing service to profile
    - DELETE /nurse/my-services/{service_id}/remove/ - Remove a service from profile
    - PATCH /nurse/my-services/{service_id}/availability/ - Update availability
    """
    permission_classes = [IsAuthenticated, IsNurse]
    
    def _get_nurse(self, request):
        """Get the nurse profile for the current user"""
        from providers.models import Nurse
        try:
            provider = request.user.provider_profile
            return provider.nurse_profile
        except Exception:
            return None
    
    def list(self, request):
        """List all services in the nurse's profile"""
        nurse = self._get_nurse(request)
        
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found. Please complete your profile first.',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get nurse's services
        nurse_services = NurseService.objects.filter(
            nurse=nurse
        ).select_related('service')
        
        # Also get available on-demand nursing services not in profile
        profile_service_ids = nurse_services.values_list('service_id', flat=True)
        available_to_add = Service.objects.filter(
            service_type=ServiceType.NURSE,
            is_on_demand=True,
            is_active=True
        ).exclude(id__in=profile_service_ids)
        
        serializer = NurseProfileServiceSerializer(nurse_services, many=True)
        available_serializer = NursingServiceSerializer(available_to_add, many=True)
        
        return Response({
            'success': True,
            'my_services': serializer.data,
            'my_services_count': nurse_services.count(),
            'available_to_add': available_serializer.data,
            'available_to_add_count': available_to_add.count(),
            'message': 'Add services to receive on-demand requests for those services'
        })
    
    @action(detail=False, methods=['post'])
    def add(self, request):
        """
        Add a nursing service to the nurse's profile.
        
        Body:
        {
            "service_id": 5,
            "custom_price": "100.00"  // Optional, overrides base price
        }
        """
        nurse = self._get_nurse(request)
        
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found. Please complete your profile first.',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        service_id = request.data.get('service_id')
        custom_price = request.data.get('custom_price')
        
        if not service_id:
            return error_response(
                ErrorCodes.SERVICE_NOT_FOUND,
                'service_id is required'
            )
        
        # Validate service exists and is a nursing on-demand service
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return error_response(
                ErrorCodes.SERVICE_NOT_FOUND,
                'Service not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if service.service_type != ServiceType.NURSE:
            return error_response(
                ErrorCodes.SERVICE_NOT_NURSING,
                'This is not a nursing service'
            )
        
        if not service.is_on_demand:
            return error_response(
                ErrorCodes.SERVICE_NOT_ON_DEMAND,
                'This service is not available for on-demand requests'
            )
        
        if not service.is_active:
            return error_response(
                ErrorCodes.SERVICE_INACTIVE,
                'This service is currently not active'
            )
        
        # Check if already added
        if NurseService.objects.filter(nurse=nurse, service=service).exists():
            return error_response(
                ErrorCodes.SERVICE_ALREADY_ADDED,
                'You have already added this service to your profile'
            )
        
        # Create the nurse service link
        nurse_service = NurseService.objects.create(
            nurse=nurse,
            service=service,
            custom_price=custom_price,
            is_available=True
        )
        
        serializer = NurseProfileServiceSerializer(nurse_service)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': f'Successfully added "{service.title}" to your profile. You will now receive requests for this service.'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='remove')
    def remove(self, request, pk=None):
        """Remove a service from the nurse's profile"""
        nurse = self._get_nurse(request)
        
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            nurse_service = NurseService.objects.get(nurse=nurse, service_id=pk)
            service_title = nurse_service.service.title
            nurse_service.delete()
            
            return Response({
                'success': True,
                'message': f'Removed "{service_title}" from your profile. You will no longer receive requests for this service.'
            })
        except NurseService.DoesNotExist:
            return error_response(
                ErrorCodes.SERVICE_NOT_IN_PROFILE,
                'This service is not in your profile',
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['patch'], url_path='availability')
    def update_availability(self, request, pk=None):
        """
        Update availability status for a service.
        
        Body:
        {
            "is_available": true,
            "custom_price": "120.00"  // Optional
        }
        """
        nurse = self._get_nurse(request)
        
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            nurse_service = NurseService.objects.get(nurse=nurse, service_id=pk)
        except NurseService.DoesNotExist:
            return error_response(
                ErrorCodes.SERVICE_NOT_IN_PROFILE,
                'This service is not in your profile',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if 'is_available' in request.data:
            nurse_service.is_available = request.data['is_available']
        
        if 'custom_price' in request.data:
            nurse_service.custom_price = request.data['custom_price']
        
        nurse_service.save()
        
        serializer = NurseProfileServiceSerializer(nurse_service)
        
        status_msg = 'available' if nurse_service.is_available else 'unavailable'
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': f'Service is now {status_msg}'
        })


# =============================================================================
# NURSE AVAILABLE REQUESTS (WITH SERVICE FILTERING)
# =============================================================================

class NurseAvailableRequestsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for nurses to view available requests in their area.
    
    IMPORTANT: Nurses will ONLY see requests for services they have added
    to their profile. If a nurse hasn't added a service, they won't see
    requests for that service.
    
    Endpoints:
    - GET /nurse/available-requests/ - List available requests (filtered by nurse's services)
    - GET /nurse/available-requests/{id}/ - Get request details
    - POST /nurse/available-requests/{id}/accept/ - Accept at patient's price
    - POST /nurse/available-requests/{id}/counter-offer/ - Make counter offer
    - POST /nurse/available-requests/{id}/reject/ - Reject request
    """
    permission_classes = [IsAuthenticated, IsNurse]
    serializer_class = NurseAvailableRequestSerializer
    
    def _get_nurse(self, request):
        """Get the nurse profile for the current user"""
        from providers.models import Nurse
        try:
            provider = request.user.provider_profile
            return provider.nurse_profile
        except Exception:
            return None
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance between two points using Haversine formula.
        Returns distance in kilometers.

        Args:
            lat1, lon1: Nurse location (Decimal)
            lat2, lon2: Request location (Decimal)

        Returns:
            Distance in kilometers (float)
        """
        from math import radians, sin, cos, sqrt, atan2
        from decimal import Decimal

        # Convert to float if Decimal
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)

        # Earth's radius in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine formula
        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        return distance

    def get_queryset(self):
        """
        Return requests in SEARCHING or NURSE_RESPONDED status
        that the nurse hasn't already responded to AND
        that match services in the nurse's profile AND
        are within the nurse's service area.
        """
        nurse = self._get_nurse(self.request)

        if not nurse:
            return NurseServiceRequest.objects.none()

        # Get service IDs that the nurse has in their profile and is available for
        nurse_service_ids = NurseService.objects.filter(
            nurse=nurse,
            is_available=True
        ).values_list('service_id', flat=True)

        # If nurse has no services, return empty queryset
        if not nurse_service_ids:
            return NurseServiceRequest.objects.none()

        # Get requests that match nurse's services
        queryset = NurseServiceRequest.objects.filter(
            status__in=[RequestStatus.SEARCHING, RequestStatus.NURSE_RESPONDED],
            service_id__in=nurse_service_ids  # Only services the nurse offers
        ).exclude(
            offers__nurse=nurse.provider  # Exclude requests nurse already responded to (NurseOffer.nurse is FK to Provider)
        ).select_related(
            'service', 'patient_user'
        ).order_by('-created_at')

        # Filter by area/distance if nurse has a location set
        nurse_provider = nurse.provider
        nurse_user = nurse_provider.user

        # Try to get nurse's primary work address
        try:
            from django.contrib.contenttypes.models import ContentType
            from address.models import Address

            nurse_address = Address.objects.get(
                content_type=ContentType.objects.get_for_model(nurse_user),
                object_id=nurse_user.id,
                address_type__in=['WORK', 'CLINIC'],
                is_primary=True
            )

            if nurse_address.latitude and nurse_address.longitude:
                # Filter requests by distance
                service_area_km = nurse.service_area_km or 50  # Default 50km
                filtered_requests = []

                for request_obj in queryset:
                    if request_obj.latitude and request_obj.longitude:
                        distance = self._calculate_distance(
                            nurse_address.latitude,
                            nurse_address.longitude,
                            request_obj.latitude,
                            request_obj.longitude
                        )

                        # Only include requests within service area
                        if distance <= service_area_km:
                            filtered_requests.append(request_obj.id)

                # Filter queryset to include only requests within service area
                queryset = queryset.filter(id__in=filtered_requests)
        except Exception:
            # If nurse doesn't have a location set, include all requests
            # User can still filter by city parameter
            pass

        # Optional: Filter by city if nurse has set a preferred city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)

        return queryset
    
    def list(self, request, *args, **kwargs):
        """List available requests with helpful info"""
        nurse = self._get_nurse(request)
        
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found. Please complete your profile first.',
                {'action': 'Complete nurse profile to view available requests'},
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if nurse has any services
        nurse_services_count = NurseService.objects.filter(
            nurse=nurse,
            is_available=True
        ).count()
        
        if nurse_services_count == 0:
            return Response({
                'success': True,
                'count': 0,
                'results': [],
                'warning': {
                    'code': ErrorCodes.SERVICE_NOT_IN_PROFILE,
                    'message': 'You have no active services in your profile. Add services to start receiving requests.',
                    'action': 'Go to /api/nurse-requests/nurse/my-services/ to add services'
                }
            })
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'results': serializer.data,
            'your_active_services_count': nurse_services_count,
            'message': f'Showing requests for your {nurse_services_count} active service(s)'
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get request details with validation"""
        nurse = self._get_nurse(request)
        
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            instance = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found or you do not offer this service',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if nurse offers this service
        if not NurseService.objects.filter(
            nurse=nurse,
            service=instance.service,
            is_available=True
        ).exists():
            return error_response(
                ErrorCodes.REQUEST_SERVICE_NOT_IN_NURSE_PROFILE,
                f'You do not offer "{instance.service.title}" service. Add it to your profile first.',
                {
                    'service_id': instance.service.id,
                    'service_name': instance.service.title,
                    'action': f'POST /api/nurse-requests/nurse/my-services/add/ with service_id={instance.service.id}'
                },
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def get_serializer_context(self):
        """Add nurse to serializer context"""
        context = super().get_serializer_context()
        context['nurse'] = self._get_nurse(self.request)
        return context
    
    def _validate_nurse_can_respond(self, nurse, request_obj):
        """Validate that nurse can respond to this request"""
        # Check nurse profile exists
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check nurse offers this service
        if not NurseService.objects.filter(
            nurse=nurse,
            service=request_obj.service,
            is_available=True
        ).exists():
            return error_response(
                ErrorCodes.REQUEST_SERVICE_NOT_IN_NURSE_PROFILE,
                f'You cannot respond to this request because you do not offer "{request_obj.service.title}" service.',
                {
                    'service_id': request_obj.service.id,
                    'service_name': request_obj.service.title,
                    'action': 'Add this service to your profile first'
                },
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already responded
        if NurseOffer.objects.filter(request=request_obj, nurse=nurse.provider).exists():
            return error_response(
                ErrorCodes.OFFER_ALREADY_SUBMITTED,
                'You have already submitted an offer for this request'
            )
        
        # Check request status
        if request_obj.status not in [RequestStatus.SEARCHING, RequestStatus.NURSE_RESPONDED]:
            return error_response(
                ErrorCodes.REQUEST_INVALID_STATUS,
                f'This request is no longer available (status: {request_obj.status})',
                {'current_status': request_obj.status}
            )
        
        return None  # No error
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept the request at the patient's offered price.
        
        Body (optional):
        {
            "estimated_arrival_time": "00:30:00",
            "notes": "I'll be there soon",
            "distance_km": 5.2
        }
        """
        nurse = self._get_nurse(request)
        
        try:
            request_obj = NurseServiceRequest.objects.get(pk=pk)
        except NurseServiceRequest.DoesNotExist:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validate nurse can respond
        validation_error = self._validate_nurse_can_respond(nurse, request_obj)
        if validation_error:
            return validation_error
        
        serializer = NurseAcceptRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            offer = NurseRequestService.nurse_accept_request(
                request_obj=request_obj,
                nurse=nurse,
                **serializer.validated_data
            )
            
            # Send signal for real-time update to patient
            nurse_offer_submitted.send(
                sender=self.__class__,
                request=request_obj,
                offer=offer,
            )
            
            return Response({
                'success': True,
                'message': 'Request accepted successfully',
                'offer_id': offer.id,
                'offered_price': str(offer.offered_price)
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return error_response(
                ErrorCodes.OFFER_NOT_AVAILABLE,
                str(e)
            )
    
    @action(detail=True, methods=['post'], url_path='counter-offer')
    def counter_offer(self, request, pk=None):
        """
        Make a counter offer with a higher price.
        
        Body:
        {
            "offered_price": 150.00,
            "estimated_arrival_time": "00:30:00",
            "notes": "Traffic is heavy",
            "distance_km": 5.2
        }
        """
        nurse = self._get_nurse(request)
        
        try:
            request_obj = NurseServiceRequest.objects.get(pk=pk)
        except NurseServiceRequest.DoesNotExist:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Validate nurse can respond
        validation_error = self._validate_nurse_can_respond(nurse, request_obj)
        if validation_error:
            return validation_error
        
        serializer = NurseCounterOfferSerializer(
            data=request.data,
            context={'request': request_obj}
        )
        
        if not serializer.is_valid():
            errors = serializer.errors
            if 'offered_price' in errors:
                return error_response(
                    ErrorCodes.PRICE_BELOW_PATIENT_OFFER,
                    f'Counter offer must be at least ${request_obj.patient_offered_price}',
                    {
                        'minimum_price': str(request_obj.patient_offered_price),
                        'your_offer': request.data.get('offered_price')
                    }
                )
            return error_response(
                'NR0001',
                'Validation failed',
                errors
            )
        
        try:
            offer = NurseRequestService.nurse_counter_offer(
                request_obj=request_obj,
                nurse=nurse,
                **serializer.validated_data
            )
            
            # Send signal for real-time update to patient
            nurse_offer_submitted.send(
                sender=self.__class__,
                request=request_obj,
                offer=offer,
            )
            
            return Response({
                'success': True,
                'message': 'Counter offer submitted successfully',
                'offer_id': offer.id,
                'offered_price': str(offer.offered_price)
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return error_response(
                ErrorCodes.OFFER_NOT_AVAILABLE,
                str(e)
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Dismiss a request without submitting an offer.
        The request is removed from this nurse's available list on subsequent
        fetches. Other nurses are unaffected.

        Body (optional):
        {
            "reason": "Too far from my location"
        }
        """
        nurse = self._get_nurse(request)

        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            request_obj = NurseServiceRequest.objects.get(pk=pk)
        except NurseServiceRequest.DoesNotExist:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Only allow rejection while the request is still open for nurse responses
        if request_obj.status not in [RequestStatus.SEARCHING, RequestStatus.NURSE_RESPONDED]:
            return error_response(
                ErrorCodes.REQUEST_INVALID_STATUS,
                f'This request is no longer available (status: {request_obj.status})',
                {'current_status': request_obj.status}
            )

        # Prevent double-response (nurse already submitted an accept or counter-offer)
        existing = NurseOffer.objects.filter(
            request=request_obj,
            nurse=nurse.provider
        ).exclude(status=OfferStatus.REJECTED).first()

        if existing:
            return error_response(
                ErrorCodes.OFFER_ALREADY_SUBMITTED,
                'You have already submitted an offer for this request'
            )

        reason = request.data.get('reason', '')

        NurseRequestService.nurse_reject_request(
            request_obj=request_obj,
            nurse=nurse,
            reason=reason,
        )

        return Response({
            'success': True,
            'message': 'Request dismissed',
        }, status=status.HTTP_200_OK)


# =============================================================================
# NURSE MY OFFERS
# =============================================================================

class NurseMyOffersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for nurses to view their submitted offers.
    
    Endpoints:
    - GET /nurse/my-offers/ - List all my offers
    - GET /nurse/my-offers/{id}/ - Get offer details
    """
    permission_classes = [IsAuthenticated, IsNurse]
    serializer_class = NurseServiceRequestDetailSerializer
    
    def _get_nurse(self, request):
        """Get the nurse profile for the current user"""
        from providers.models import Nurse
        try:
            provider = request.user.provider_profile
            return provider.nurse_profile
        except Exception:
            return None
    
    def get_queryset(self):
        """
        Return all requests where nurse has submitted an offer (full history).
        
        This includes:
        - Requests where nurse offer was accepted
        - Requests where nurse offer was rejected (patient chose another nurse)
        - Requests where nurse counter-offered but patient rejected
        - Requests where patient cancelled after nurse submitted offer
        - All pending offers
        
        Query Parameters:
        - status: Filter by request status (e.g., COMPLETED, CANCELLED)
        - offer_status: Filter by nurse's offer status (PENDING, ACCEPTED, REJECTED)
        - is_active: Filter active requests only
        - is_history: Filter historical requests only (COMPLETED, CANCELLED)
        """
        nurse = self._get_nurse(self.request)
        
        if not nurse:
            return NurseServiceRequest.objects.none()
        
        queryset = NurseServiceRequest.objects.filter(
            offers__nurse=nurse.provider  # NurseOffer.nurse is FK to Provider
        ).select_related(
            'service', 'patient_user', 'accepted_nurse__user'
        ).prefetch_related(
            'offers__nurse__user'
        ).distinct().order_by('-created_at')
        
        # Filter by request status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        
        # Filter by nurse's offer status
        offer_status = self.request.query_params.get('offer_status')
        if offer_status:
            queryset = queryset.filter(
                offers__nurse=nurse.provider,
                offers__status=offer_status.upper()
            )
        
        # Filter active vs historical
        is_active = self.request.query_params.get('is_active')
        is_history = self.request.query_params.get('is_history')
        
        active_statuses = [
            RequestStatus.CREATED, RequestStatus.SEARCHING, 
            RequestStatus.NURSE_RESPONDED, RequestStatus.PATIENT_DECISION,
            RequestStatus.ACCEPTED, RequestStatus.IN_PROGRESS
        ]
        history_statuses = [RequestStatus.COMPLETED, RequestStatus.CANCELLED]
        
        if is_active and is_active.lower() == 'true':
            queryset = queryset.filter(status__in=active_statuses)
        elif is_history and is_history.lower() == 'true':
            queryset = queryset.filter(status__in=history_statuses)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List nurse's offers with summary"""
        nurse = self._get_nurse(request)
        
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Get stats
        from django.db.models import Count
        stats = {
            'total_offers': queryset.count(),
            'pending': queryset.filter(offers__nurse=nurse.provider, offers__status=OfferStatus.PENDING).distinct().count(),
            'accepted': queryset.filter(accepted_nurse=nurse.provider).count(),
        }
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'results': serializer.data,
            'stats': stats
        })


# =============================================================================
# NURSE REQUEST HISTORY
# =============================================================================

class NurseRequestHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for nurses to view their request history (accepted, declined, completed requests).

    Endpoints:
    - GET /nurse/request-history/ - List request history with filtering
    - GET /nurse/request-history/{id}/ - Get history detail

    Query Parameters:
    - status: Filter by request status (ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED)
    - date_from: Filter requests from date (ISO 8601: YYYY-MM-DD)
    - date_to: Filter requests until date (ISO 8601: YYYY-MM-DD)
    - patient_name: Filter by partial patient name
    - ordering: Sort by field (e.g., -completed_at, final_price)
    - page: Pagination page number
    - page_size: Results per page (default 20)
    """
    permission_classes = [IsAuthenticated, IsNurse]
    serializer_class = NurseRequestHistorySerializer
    pagination_class = None  # Use default pagination from settings

    def get_queryset(self):
        """Get nurse's request history."""
        nurse = self._get_nurse(self.request)
        if not nurse:
            return NurseServiceRequest.objects.none()

        # Get all requests where this nurse was accepted (invited to service)
        queryset = NurseServiceRequest.objects.filter(
            accepted_nurse=nurse.provider
        ).select_related(
            'service', 'patient_user', 'patient_record', 'accepted_nurse__user'
        ).order_by('-created_at')

        # Filter by request status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            try:
                from datetime import datetime
                date_from_dt = datetime.fromisoformat(date_from).date()
                queryset = queryset.filter(completed_at__date__gte=date_from_dt)
            except (ValueError, TypeError):
                pass

        date_to = self.request.query_params.get('date_to')
        if date_to:
            try:
                from datetime import datetime
                date_to_dt = datetime.fromisoformat(date_to).date()
                queryset = queryset.filter(completed_at__date__lte=date_to_dt)
            except (ValueError, TypeError):
                pass

        # Filter by patient name (partial match)
        patient_name = self.request.query_params.get('patient_name')
        if patient_name:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(patient_record__first_name__icontains=patient_name) |
                Q(patient_record__last_name__icontains=patient_name) |
                Q(patient_user__first_name__icontains=patient_name) |
                Q(patient_user__last_name__icontains=patient_name)
            )

        # Handle ordering
        ordering = self.request.query_params.get('ordering', '-completed_at')
        queryset = queryset.order_by(ordering)

        return queryset

    def _get_nurse(self, request):
        """Get nurse profile from request user."""
        try:
            nurse = Nurse.objects.get(provider__user=request.user)
            return nurse
        except Nurse.DoesNotExist:
            return None

    def list(self, request, *args, **kwargs):
        """List nurse's request history with stats."""
        nurse = self._get_nurse(request)

        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        queryset = self.get_queryset()

        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'results': serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)

        # Get stats
        all_requests = NurseServiceRequest.objects.filter(accepted_nurse=nurse.provider)
        stats = {
            'total_accepted': all_requests.filter(status=RequestStatus.ACCEPTED).count(),
            'total_in_progress': all_requests.filter(status=RequestStatus.IN_PROGRESS).count(),
            'total_completed': all_requests.filter(status=RequestStatus.COMPLETED).count(),
            'total_cancelled': all_requests.filter(status=RequestStatus.CANCELLED).count(),
        }

        return Response({
            'success': True,
            'count': queryset.count(),
            'results': serializer.data,
            'stats': stats
        })

    def retrieve(self, request, pk=None):
        """Get detailed view of a request from history."""
        try:
            request_obj = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verify this nurse was accepted for this request
        nurse = self._get_nurse(request)
        if not nurse or request_obj.accepted_nurse != nurse.provider:
            return error_response(
                ErrorCodes.REQUEST_NOT_OWNER,
                'You do not have permission to view this request',
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(request_obj)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Nurse marks the service as started (IN_PROGRESS).

        POST /api/nurse-requests/nurse/request-history/{id}/start/

        Requirements:
        - Authenticated nurse must be the accepted_nurse on the request.
        - Request must be in ACCEPTED status.
        """
        nurse = self._get_nurse(request)
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            request_obj = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        if request_obj.accepted_nurse != nurse.provider:
            return error_response(
                ErrorCodes.REQUEST_NOT_OWNER,
                'You are not the assigned nurse for this request',
                status_code=status.HTTP_403_FORBIDDEN
            )

        old_status = request_obj.status
        try:
            updated_request = NurseRequestService.start_service(request_obj)
            request_status_changed.send(
                sender=self.__class__,
                request=updated_request,
                old_status=old_status,
                new_status=updated_request.status,
            )
            from .serializers import NurseServiceRequestDetailSerializer
            return Response({
                'success': True,
                'data': NurseServiceRequestDetailSerializer(updated_request).data,
                'message': 'Service started',
            })
        except ValueError as e:
            return error_response(ErrorCodes.REQUEST_INVALID_STATUS, str(e))

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Nurse marks the service as completed (COMPLETED).

        POST /api/nurse-requests/nurse/request-history/{id}/complete/

        Requirements:
        - Authenticated nurse must be the accepted_nurse on the request.
        - Request must be in IN_PROGRESS status.
        """
        nurse = self._get_nurse(request)
        if not nurse:
            return error_response(
                ErrorCodes.NURSE_PROFILE_NOT_FOUND,
                'Nurse profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            request_obj = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        if request_obj.accepted_nurse != nurse.provider:
            return error_response(
                ErrorCodes.REQUEST_NOT_OWNER,
                'You are not the assigned nurse for this request',
                status_code=status.HTTP_403_FORBIDDEN
            )

        old_status = request_obj.status
        try:
            updated_request = NurseRequestService.complete_service(request_obj)
            request_status_changed.send(
                sender=self.__class__,
                request=updated_request,
                old_status=old_status,
                new_status=updated_request.status,
            )
            from .serializers import NurseServiceRequestDetailSerializer
            return Response({
                'success': True,
                'data': NurseServiceRequestDetailSerializer(updated_request).data,
                'message': 'Service completed successfully',
            })
        except ValueError as e:
            return error_response(ErrorCodes.REQUEST_INVALID_STATUS, str(e))

    @action(detail=True, methods=['get'], url_path='patient-folder')
    def patient_folder(self, request, pk=None):
        """
        View the patient's medical folder for an accepted/in-progress/completed request.
        Only the nurse who was accepted for the request may access this.
        Returns non-confidential medical records plus key clinical demographics.

        GET /api/nurse-requests/nurse/request-history/{id}/patient-folder/
        """
        try:
            request_obj = self.get_object()
        except Exception:
            return error_response(
                ErrorCodes.REQUEST_NOT_FOUND,
                'Request not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        nurse = self._get_nurse(request)
        if not nurse or request_obj.accepted_nurse != nurse.provider:
            return error_response(
                ErrorCodes.REQUEST_NOT_OWNER,
                'You do not have permission to view this patient\'s medical folder',
                status_code=status.HTTP_403_FORBIDDEN
            )

        allowed_statuses = [
            RequestStatus.ACCEPTED,
            RequestStatus.IN_PROGRESS,
            RequestStatus.COMPLETED,
        ]
        if request_obj.status not in allowed_statuses:
            return error_response(
                ErrorCodes.REQUEST_INVALID_STATUS,
                'The patient\'s medical folder is only accessible for accepted or completed requests',
                {'current_status': request_obj.status}
            )

        from medical_record.models import MedicalRecord, MedicalRecordAccessLog
        from medical_record.serializers import MedicalRecordListSerializer
        from django.db import models as db_models
        from datetime import timedelta as _timedelta

        patient_user = request_obj.patient_user
        patient_record = request_obj.patient_record

        if patient_user:
            records_qs = MedicalRecord.objects.filter(
                db_models.Q(patient=patient_user) |
                db_models.Q(patient_record__linked_user=patient_user),
                is_active=True,
                is_confidential=False,
            ).select_related('prescription', 'allergy').order_by('-record_date', '-created_at')
        elif patient_record:
            records_qs = MedicalRecord.objects.filter(
                patient_record=patient_record,
                is_active=True,
                is_confidential=False,
            ).select_related('prescription', 'allergy').order_by('-record_date', '-created_at')
        else:
            records_qs = MedicalRecord.objects.none()

        # Log access for each record viewed
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        client_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        for rec in records_qs:
            try:
                MedicalRecordAccessLog.objects.create(
                    medical_record=rec,
                    accessed_by=request.user,
                    access_type='VIEW',
                    ip_address=client_ip,
                )
            except Exception:
                pass

        # Clinical demographics
        patient_info = {}
        pr = patient_record
        if pr is None and patient_user:
            try:
                pr = patient_user.patient_record
            except Exception:
                pass
        if pr:
            patient_info = {
                'blood_type': pr.blood_type or 'UNKNOWN',
                'known_allergies': pr.known_allergies or '',
                'chronic_conditions': pr.chronic_conditions or '',
                'current_medications': pr.current_medications or '',
                'emergency_contact_name': pr.emergency_contact_name or '',
                'emergency_contact_phone': pr.emergency_contact_phone or '',
            }

        records_data = MedicalRecordListSerializer(records_qs, many=True, context={'request': request}).data

        by_type = {}
        active_allergies = []
        from django.utils import timezone as _tz
        thirty_days_ago = _tz.now().date() - _timedelta(days=30)
        recent_records = []

        for r in records_data:
            rt = r.get('record_type')
            by_type.setdefault(rt, []).append(r)
            if rt == 'ALLERGY':
                active_allergies.append(r)
            if r.get('record_date') and r['record_date'] >= str(thirty_days_ago):
                recent_records.append(r)

        critical_records = [r for r in records_data if r.get('severity_level') in ('CRITICAL', 'HIGH')]

        return Response({
            'success': True,
            'data': {
                'request_id': request_obj.id,
                'access_note': 'Confidential records are excluded. Access is logged.',
                'patient_clinical_info': patient_info,
                'summary': {
                    'total_records': len(records_data),
                    'active_allergies': len(active_allergies),
                    'critical_or_high': len(critical_records),
                    'recent_30_days': len(recent_records),
                    'record_types': {k: len(v) for k, v in by_type.items()},
                },
                'medical_records': {
                    'timeline': records_data,
                    'by_type': by_type,
                    'active_allergies': active_allergies,
                    'critical_or_high': critical_records,
                    'recent_30_days': recent_records,
                },
            }
        })
