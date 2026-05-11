from rest_framework import serializers
from decimal import Decimal
from datetime import timedelta
from .models import (
    NurseServiceRequest,
    NurseOffer,
    RequestHistory,
    RequestStatus,
    OfferStatus
)
from services.models import Service, ServiceType


class NursingServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for nursing services catalog.
    Uses the main Service model filtered for nursing on-demand services.
    """
    # Map Service fields to match the original NursingService API
    name = serializers.CharField(source='title', read_only=True)
    base_price = serializers.DecimalField(source='price', max_digits=10, decimal_places=2, read_only=True)
    estimated_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'base_price',
            'estimated_duration', 'is_active', 'icon',
            'currency', 'is_home_service',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_estimated_duration(self, obj):
        """Convert duration_minutes to timedelta string format"""
        if obj.duration_minutes:
            td = timedelta(minutes=obj.duration_minutes)
            total_seconds = int(td.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return None


class NurseOfferSerializer(serializers.ModelSerializer):
    """Serializer for nurse offers with nurse details"""
    nurse_name = serializers.SerializerMethodField()
    nurse_rating = serializers.SerializerMethodField()
    nurse_review_count = serializers.SerializerMethodField()
    nurse_profile_image = serializers.SerializerMethodField()
    nurse_id = serializers.IntegerField(source='nurse.id', read_only=True)
    nurse_years_experience = serializers.SerializerMethodField()
    nurse_completed_services = serializers.SerializerMethodField()
    nurse_biography = serializers.SerializerMethodField()
    nurse_is_verified = serializers.SerializerMethodField()
    
    class Meta:
        model = NurseOffer
        fields = [
            'id', 'nurse_id', 'nurse_name', 'nurse_rating', 'nurse_review_count',
            'nurse_profile_image', 'nurse_years_experience', 'nurse_completed_services',
            'nurse_biography', 'nurse_is_verified',
            'offered_price', 'status',
            'estimated_arrival_time', 'distance_km', 'notes',
            'created_at', 'responded_at'
        ]
        read_only_fields = [
            'id', 'nurse_id', 'nurse_name', 'nurse_rating', 'nurse_review_count',
            'nurse_profile_image', 'nurse_years_experience', 'nurse_completed_services',
            'nurse_biography', 'nurse_is_verified', 'created_at', 'responded_at'
        ]
    
    def get_nurse_name(self, obj):
        """Get nurse full name."""
        if hasattr(obj.nurse, 'nurse_profile'):
            nurse = obj.nurse.nurse_profile
            name = f"{nurse.first_name} {nurse.last_name}".strip()
            if name:
                return name
        return obj.nurse.user.email.split('@')[0]
    
    def get_nurse_rating(self, obj):
        """Get nurse average rating from reviews system."""
        try:
            from reviews.models import get_review_aggregate
            aggregate = get_review_aggregate(obj.nurse)
            return float(aggregate.average_rating)
        except Exception:
            return 0.0
    
    def get_nurse_review_count(self, obj):
        """Get total number of reviews for this nurse."""
        try:
            from reviews.models import get_review_aggregate
            aggregate = get_review_aggregate(obj.nurse)
            return aggregate.review_count
        except Exception:
            return 0
    
    def get_nurse_profile_image(self, obj):
        """Return actual profile image URL."""
        if hasattr(obj.nurse, 'nurse_profile') and obj.nurse.nurse_profile.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.nurse.nurse_profile.profile_image.url)
            return obj.nurse.nurse_profile.profile_image.url
        return None
    
    def get_nurse_years_experience(self, obj):
        """Get nurse years of experience."""
        if hasattr(obj.nurse, 'nurse_profile'):
            return obj.nurse.nurse_profile.years_of_experience
        return None
    
    def get_nurse_completed_services(self, obj):
        """Count completed nurse service requests."""
        from nurse_requests.models import NurseServiceRequest, RequestStatus
        return NurseServiceRequest.objects.filter(
            accepted_nurse=obj.nurse,
            status=RequestStatus.COMPLETED
        ).count()
    
    def get_nurse_biography(self, obj):
        """Get nurse biography snippet."""
        if hasattr(obj.nurse, 'nurse_profile'):
            bio = obj.nurse.nurse_profile.biography or ''
            if len(bio) > 150:
                return bio[:150] + '...'
            return bio
        return ''
    
    def get_nurse_is_verified(self, obj):
        """Check if nurse is verified."""
        if hasattr(obj.nurse, 'nurse_profile'):
            return obj.nurse.nurse_profile.is_verified
        return False


class NurseServiceRequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing requests"""
    service_name = serializers.CharField(source='service.title', read_only=True)
    patient_name = serializers.SerializerMethodField()
    offers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = NurseServiceRequest
        fields = [
            'id', 'service_name', 'patient_name', 'status',
            'patient_offered_price', 'final_price', 'city',
            'latitude', 'longitude', 'offers_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_patient_name(self, obj):
        return obj.get_patient_display_name()
    
    def get_offers_count(self, obj):
        return obj.offers.count()


class NurseServiceRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for request with all related data"""
    service = NursingServiceSerializer(read_only=True)
    offers = NurseOfferSerializer(many=True, read_only=True)
    patient_name = serializers.SerializerMethodField()
    accepted_nurse_name = serializers.SerializerMethodField()
    accepted_nurse_profile = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()
    can_leave_review = serializers.SerializerMethodField()
    
    class Meta:
        model = NurseServiceRequest
        fields = [
            'id', 'patient_user', 'patient_record', 'patient_name', 'service',
            'accepted_nurse', 'accepted_nurse_name', 'accepted_nurse_profile',
            'base_price', 'patient_offered_price', 'final_price',
            'address', 'address_details',
            'latitude', 'longitude', 'city', 'state', 'address_line', 'country',
            'status', 'notes', 'offers',
            'created_at', 'updated_at', 'accepted_at',
            'started_at', 'completed_at', 'cancelled_at',
            'cancellation_reason', 'can_leave_review'
        ]
        read_only_fields = [
            'id', 'patient_user', 'patient_record', 'base_price', 'accepted_nurse',
            'final_price', 'created_at', 'updated_at',
            'accepted_at', 'started_at', 'completed_at',
            'cancelled_at'
        ]
    
    def get_patient_name(self, obj):
        return obj.get_patient_display_name()
    
    def get_accepted_nurse_name(self, obj):
        if obj.accepted_nurse and hasattr(obj.accepted_nurse, 'nurse_profile'):
            nurse = obj.accepted_nurse.nurse_profile
            return f"{nurse.first_name} {nurse.last_name}".strip()
        return None
    
    def get_accepted_nurse_profile(self, obj):
        """Get summary of accepted nurse for quick display."""
        if not obj.accepted_nurse:
            return None
        
        nurse = obj.accepted_nurse
        profile = {}
        
        if hasattr(nurse, 'nurse_profile'):
            np = nurse.nurse_profile
            profile['first_name'] = np.first_name
            profile['last_name'] = np.last_name
            profile['phone_number'] = np.phone_number
            if np.profile_image:
                request = self.context.get('request')
                if request:
                    profile['profile_image'] = request.build_absolute_uri(np.profile_image.url)
                else:
                    profile['profile_image'] = np.profile_image.url
        
        # Get rating and recent reviews
        try:
            from reviews.models import get_review_aggregate, get_reviews_for_object
            aggregate = get_review_aggregate(nurse)
            profile['average_rating'] = float(aggregate.average_rating)
            profile['review_count'] = aggregate.review_count
            profile['rating_distribution'] = {
                1: aggregate.rating_1_count,
                2: aggregate.rating_2_count,
                3: aggregate.rating_3_count,
                4: aggregate.rating_4_count,
                5: aggregate.rating_5_count,
            }
            reviews = get_reviews_for_object(nurse)[:3]
            profile['recent_reviews'] = [
                {
                    'id': str(r.id),
                    'rating': r.rating,
                    'text': r.text[:200] if r.text else '',
                    'created_at': r.created_at.isoformat(),
                    'has_response': bool(r.response),
                }
                for r in reviews
            ]
        except Exception:
            profile['average_rating'] = 0.0
            profile['review_count'] = 0
            profile['rating_distribution'] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            profile['recent_reviews'] = []

        return profile
    
    def get_address_details(self, obj):
        """Get linked address details if available."""
        if obj.address:
            return {
                'id': obj.address.id,
                'street': obj.address.street,
                'city': obj.address.city,
                'state': obj.address.state,
                'zip_code': obj.address.zip_code,
                'country': obj.address.country,
                'latitude': str(obj.address.latitude) if obj.address.latitude else None,
                'longitude': str(obj.address.longitude) if obj.address.longitude else None,
                'address_type': obj.address.address_type,
            }
        return None
    
    def get_can_leave_review(self, obj):
        """Check if patient can leave a review (completed & not reviewed yet)."""
        if obj.status != RequestStatus.COMPLETED or not obj.accepted_nurse:
            return False
        
        try:
            from reviews.models import Review, ReviewStatus
            from django.contrib.contenttypes.models import ContentType
            
            # Check if review already exists for this request context
            request_ct = ContentType.objects.get_for_model(obj)
            provider_ct = ContentType.objects.get_for_model(obj.accepted_nurse)
            
            exists = Review.objects.filter(
                reviewed_content_type=provider_ct,
                reviewed_object_id=str(obj.accepted_nurse.id),
                context_content_type=request_ct,
                context_object_id=str(obj.id),
                status=ReviewStatus.ACTIVE
            ).exists()
            
            return not exists
        except Exception:
            return False


class CreateNurseServiceRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating a new nurse service request"""
    
    class Meta:
        model = NurseServiceRequest
        fields = [
            'service', 'patient_offered_price',
            'latitude', 'longitude', 'city',
            'address_line', 'notes'
        ]
    
    def validate_patient_offered_price(self, value):
        """Ensure offered price is >= base price"""
        service_id = self.initial_data.get('service')
        if service_id:
            try:
                service = Service.objects.get(id=service_id)
                if value < service.price:
                    raise serializers.ValidationError(
                        f"Offered price ({value:.2f} DZD) cannot be lower than "
                        f"base price ({service.price:.2f} DZD)"
                    )
            except Service.DoesNotExist:
                raise serializers.ValidationError("Invalid service selected")
        return value
    
    def validate_service(self, value):
        """Ensure service is active, is a nursing service, and supports on-demand"""
        if not value.is_active:
            raise serializers.ValidationError("This service is not currently available")
        if value.service_type != ServiceType.NURSE:
            raise serializers.ValidationError("This service is not a nursing service")
        if not value.is_on_demand:
            raise serializers.ValidationError("This service is not available for on-demand requests")
        return value
    
    def create(self, validated_data):
        """Create request with base_price from service"""
        service = validated_data['service']
        validated_data['base_price'] = service.price  # Use price as base_price
        validated_data['status'] = RequestStatus.CREATED
        return super().create(validated_data)


class AcceptOfferSerializer(serializers.Serializer):
    """Serializer for patient accepting a nurse offer"""
    offer_id = serializers.IntegerField()
    
    def validate_offer_id(self, value):
        """Ensure offer exists and belongs to this request"""
        request = self.context.get('request_obj')
        try:
            offer = NurseOffer.objects.get(id=value, request=request)
            if offer.status not in (OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED):
                raise serializers.ValidationError("This offer is no longer available")
        except NurseOffer.DoesNotExist:
            raise serializers.ValidationError("Invalid offer selected")
        return value


class NurseAcceptRequestSerializer(serializers.Serializer):
    """Serializer for nurse accepting request at patient's price"""
    estimated_arrival_time = serializers.DurationField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    distance_km = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False
    )


class NurseCounterOfferSerializer(serializers.Serializer):
    """Serializer for nurse making a counter offer"""
    offered_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_arrival_time = serializers.DurationField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    distance_km = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False
    )
    
    def validate_offered_price(self, value):
        """Ensure counter offer is >= patient's offered price"""
        request = self.context.get('request')
        if value < request.patient_offered_price:
            raise serializers.ValidationError(
                f"Counter offer ({value:.2f} DZD) must be at least "
                f"{request.patient_offered_price:.2f} DZD"
            )
        if value < request.base_price:
            raise serializers.ValidationError(
                f"Counter offer ({value:.2f} DZD) cannot be lower than "
                f"base price ({request.base_price:.2f} DZD)"
            )
        return value


class CancelRequestSerializer(serializers.Serializer):
    """Serializer for cancelling a request"""
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)


class RequestHistorySerializer(serializers.ModelSerializer):
    """Serializer for request history/audit trail"""
    actor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RequestHistory
        fields = [
            'id', 'action', 'actor', 'actor_name',
            'old_status', 'new_status', 'details', 'timestamp'
        ]
        read_only_fields = fields
    
    def get_actor_name(self, obj):
        if obj.actor:
            return f"{obj.actor.first_name} {obj.actor.last_name}".strip()
        return "System"


class NurseAvailableRequestSerializer(serializers.ModelSerializer):
    """Serializer for nurses viewing available requests in their area"""
    service_name = serializers.CharField(source='service.title', read_only=True)
    service_description = serializers.CharField(source='service.description', read_only=True)
    service_id = serializers.IntegerField(source='service.id', read_only=True)
    patient_name = serializers.SerializerMethodField()
    my_offer = serializers.SerializerMethodField()
    patient_rating = serializers.SerializerMethodField()
    patient_review_count = serializers.SerializerMethodField()
    patient_clinical_summary = serializers.SerializerMethodField()

    class Meta:
        model = NurseServiceRequest
        fields = [
            'id', 'service_id', 'service_name', 'service_description',
            'patient_name', 'patient_offered_price', 'base_price',
            'latitude', 'longitude', 'city', 'address_line',
            'status', 'created_at', 'my_offer',
            'patient_rating', 'patient_review_count', 'patient_clinical_summary',
        ]
        read_only_fields = fields

    def get_patient_name(self, obj):
        name = obj.get_patient_display_name()
        if name and len(name) > 1:
            parts = name.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[-1][0]}."
        return name

    def get_patient_rating(self, obj):
        """Overall rating the patient has received from nurses."""
        try:
            from reviews.models import get_review_aggregate
            patient_user = obj.get_patient_user()
            if patient_user:
                aggregate = get_review_aggregate(patient_user)
                return float(aggregate.average_rating)
        except Exception:
            pass
        return None

    def get_patient_review_count(self, obj):
        """Total number of reviews the patient has received."""
        try:
            from reviews.models import get_review_aggregate
            patient_user = obj.get_patient_user()
            if patient_user:
                aggregate = get_review_aggregate(patient_user)
                return aggregate.review_count
        except Exception:
            pass
        return 0

    def get_patient_clinical_summary(self, obj):
        """
        Basic clinical info needed before accepting care.
        Only blood type, allergies, and chronic conditions — no confidential data.
        """
        pr = None
        if obj.patient_record:
            pr = obj.patient_record
        elif obj.patient_user:
            try:
                pr = obj.patient_user.patient_record
            except Exception:
                pass
        if pr:
            return {
                'blood_type': pr.blood_type or 'UNKNOWN',
                'known_allergies': pr.known_allergies or '',
                'chronic_conditions': pr.chronic_conditions or '',
            }
        return None

    def get_my_offer(self, obj):
        """Get the current nurse's offer if exists"""
        nurse = self.context.get('nurse')
        if nurse:
            try:
                offer = obj.offers.get(nurse=nurse.provider)
                return NurseOfferSerializer(offer).data
            except NurseOffer.DoesNotExist:
                return None
        return None


# =============================================================================
# NURSE PROFILE SERVICES SERIALIZERS
# =============================================================================

class NurseProfileServiceSerializer(serializers.Serializer):
    """Serializer for nurse's profile services"""
    id = serializers.IntegerField(source='service.id', read_only=True)
    service_id = serializers.IntegerField(source='service.id', read_only=True)
    title = serializers.CharField(source='service.title', read_only=True)
    description = serializers.CharField(source='service.description', read_only=True)
    base_price = serializers.DecimalField(
        source='service.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    custom_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
        required=False
    )
    effective_price = serializers.SerializerMethodField()
    duration_minutes = serializers.IntegerField(source='service.duration_minutes', read_only=True)
    is_available = serializers.BooleanField()
    is_on_demand = serializers.BooleanField(source='service.is_on_demand', read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    def get_effective_price(self, obj):
        """Return custom price if set, otherwise base price formatted in DZD"""
        price = obj.custom_price if obj.custom_price else obj.service.price
        return f"{float(price):.2f} DZD"


# =============================================================================
# PATIENT SAVED ADDRESS SERIALIZER
# =============================================================================

class PatientSavedAddressSerializer(serializers.Serializer):
    """Serializer for patient's saved addresses"""
    id = serializers.IntegerField(read_only=True)
    street = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    state = serializers.CharField(read_only=True)
    zip_code = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, read_only=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, read_only=True)
    is_primary = serializers.BooleanField(read_only=True)
    address_type = serializers.CharField(read_only=True)
    full_address = serializers.SerializerMethodField()
    has_coordinates = serializers.SerializerMethodField()
    
    def get_full_address(self, obj):
        """Return formatted full address"""
        parts = [obj.street, obj.city, obj.state, obj.country]
        return ', '.join([p for p in parts if p])
    
    def get_has_coordinates(self, obj):
        """Check if address has valid coordinates for map selection"""
        return bool(obj.latitude and obj.longitude)


# =============================================================================
# NURSE PROFILE DETAIL SERIALIZER (for patient to view before selection)
# =============================================================================

class NurseProfileDetailSerializer(serializers.Serializer):
    """
    Comprehensive serializer for viewing a nurse's full profile.
    Used when patients want to see detailed nurse info before selection.
    """
    # Basic info
    id = serializers.IntegerField(source='provider.id', read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.SerializerMethodField()
    profile_image = serializers.ImageField(read_only=True)
    biography = serializers.CharField(read_only=True)
    
    # Professional info
    license_number = serializers.CharField(read_only=True)
    certification = serializers.CharField(read_only=True)
    years_of_experience = serializers.IntegerField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    is_home_service_available = serializers.BooleanField(read_only=True)
    
    # Ratings & Reviews (from reviews app)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    rating_distribution = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    
    # Service history
    completed_services_count = serializers.SerializerMethodField()
    services_offered = serializers.SerializerMethodField()
    
    def get_full_name(self, obj):
        """Get formatted full name."""
        return f"{obj.first_name} {obj.last_name}".strip() or "Nurse"
    
    def get_average_rating(self, obj):
        """Get average rating from reviews system."""
        try:
            from reviews.models import get_review_aggregate
            aggregate = get_review_aggregate(obj.provider)
            return float(aggregate.average_rating)
        except Exception:
            return 0.0
    
    def get_review_count(self, obj):
        """Get total review count."""
        try:
            from reviews.models import get_review_aggregate
            aggregate = get_review_aggregate(obj.provider)
            return aggregate.review_count
        except Exception:
            return 0
    
    def get_rating_distribution(self, obj):
        """Get rating distribution."""
        try:
            from reviews.models import get_review_aggregate
            aggregate = get_review_aggregate(obj.provider)
            return {
                1: aggregate.rating_1_count,
                2: aggregate.rating_2_count,
                3: aggregate.rating_3_count,
                4: aggregate.rating_4_count,
                5: aggregate.rating_5_count,
            }
        except Exception:
            return {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    def get_recent_reviews(self, obj):
        """Get recent reviews for this nurse."""
        try:
            from reviews.models import get_reviews_for_object
            reviews = get_reviews_for_object(obj.provider)[:5]
            return [{
                'id': str(review.id),
                'rating': review.rating,
                'text': review.text[:200] if review.text else '',
                'created_at': review.created_at.isoformat(),
                'has_response': bool(review.response),
            } for review in reviews]
        except Exception:
            return []
    
    def get_completed_services_count(self, obj):
        """Count completed nurse service requests."""
        from nurse_requests.models import NurseServiceRequest, RequestStatus
        return NurseServiceRequest.objects.filter(
            accepted_nurse=obj.provider,
            status=RequestStatus.COMPLETED
        ).count()
    
    def get_services_offered(self, obj):
        """Get list of services this nurse offers."""
        try:
            from services.models import NurseService
            nurse_services = NurseService.objects.filter(
                nurse=obj,
                is_available=True
            ).select_related('service')[:10]
            return [{
                'id': ns.service.id,
                'title': ns.service.title,
                'price': f"{float(ns.custom_price or ns.service.price):.2f} DZD",
                'duration_minutes': ns.service.duration_minutes,
            } for ns in nurse_services]
        except Exception:
            return []


class NurseRequestHistorySerializer(serializers.ModelSerializer):
    """Serializer for nurse's request history with filtering and history details."""
    service_name = serializers.CharField(source='service.title', read_only=True)
    patient_name = serializers.SerializerMethodField()
    patient_initials = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_leave_review = serializers.SerializerMethodField()
    nurse_review = serializers.SerializerMethodField()
    patient_review = serializers.SerializerMethodField()
    patient_overall_rating = serializers.SerializerMethodField()
    patient_total_reviews = serializers.SerializerMethodField()

    class Meta:
        model = NurseServiceRequest
        fields = [
            'id', 'service_name', 'patient_name', 'patient_initials',
            'status', 'status_display', 'final_price', 'base_price',
            'accepted_at', 'started_at', 'completed_at', 'cancelled_at',
            'cancellation_reason', 'city',
            'can_leave_review', 'nurse_review', 'patient_review',
            'patient_overall_rating', 'patient_total_reviews',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_patient_name(self, obj):
        """Get anonymized patient name for privacy."""
        name = obj.get_patient_display_name()
        if name and len(name) > 2:
            # Show first initial and last initial
            return f"{name[0]}. {name.split()[-1] if ' ' in name else 'P.'}"
        return "Patient"

    def get_patient_initials(self, obj):
        """Get patient initials for avatar."""
        name = obj.get_patient_display_name()
        if name:
            parts = name.split()
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[-1][0]}"
            else:
                return name[:2]
        return "P"

    def get_can_leave_review(self, obj):
        """Check if nurse can leave a review (completed & not reviewed yet)."""
        if obj.status != RequestStatus.COMPLETED or not obj.accepted_nurse:
            return False

        try:
            from reviews.models import Review, ReviewStatus
            from django.contrib.contenttypes.models import ContentType

            # Check if nurse (provider) already reviewed patient
            patient_user = obj.get_patient_user()
            if not patient_user:
                return False

            patient_ct = ContentType.objects.get_for_model(patient_user)
            request_ct = ContentType.objects.get_for_model(obj)

            # Look for nurse's review of patient for this request
            exists = Review.objects.filter(
                reviewer=obj.accepted_nurse.user,
                reviewed_content_type=patient_ct,
                reviewed_object_id=str(patient_user.id),
                context_content_type=request_ct,
                context_object_id=str(obj.id),
                status=ReviewStatus.ACTIVE
            ).exists()

            return not exists
        except Exception:
            return False

    def get_patient_overall_rating(self, obj):
        """Patient's aggregate rating across all nurse requests."""
        try:
            from reviews.models import get_review_aggregate
            patient_user = obj.get_patient_user()
            if patient_user:
                aggregate = get_review_aggregate(patient_user)
                return float(aggregate.average_rating)
        except Exception:
            pass
        return None

    def get_patient_total_reviews(self, obj):
        """Total number of reviews the patient has received from nurses."""
        try:
            from reviews.models import get_review_aggregate
            patient_user = obj.get_patient_user()
            if patient_user:
                aggregate = get_review_aggregate(patient_user)
                return aggregate.review_count
        except Exception:
            pass
        return 0

    def get_nurse_review(self, obj):
        """Get review submitted by nurse to patient."""
        try:
            from reviews.models import Review, ReviewStatus
            from django.contrib.contenttypes.models import ContentType

            if not obj.accepted_nurse or obj.status != RequestStatus.COMPLETED:
                return None

            patient_user = obj.get_patient_user()
            if not patient_user:
                return None

            patient_ct = ContentType.objects.get_for_model(patient_user)
            request_ct = ContentType.objects.get_for_model(obj)

            review = Review.objects.filter(
                reviewer=obj.accepted_nurse.user,
                reviewed_content_type=patient_ct,
                reviewed_object_id=str(patient_user.id),
                context_content_type=request_ct,
                context_object_id=str(obj.id),
                status=ReviewStatus.ACTIVE
            ).first()

            if review:
                return {
                    'id': str(review.id),
                    'rating': review.rating,
                    'text': review.text[:150] if review.text else '',
                    'created_at': review.created_at.isoformat(),
                }
        except Exception:
            pass
        return None

    def get_patient_review(self, obj):
        """Get review submitted by patient to nurse."""
        try:
            from reviews.models import Review, ReviewStatus
            from django.contrib.contenttypes.models import ContentType

            if not obj.accepted_nurse or obj.status != RequestStatus.COMPLETED:
                return None

            nurse_ct = ContentType.objects.get_for_model(obj.accepted_nurse)
            request_ct = ContentType.objects.get_for_model(obj)

            review = Review.objects.filter(
                reviewed_content_type=nurse_ct,
                reviewed_object_id=str(obj.accepted_nurse.id),
                context_content_type=request_ct,
                context_object_id=str(obj.id),
                status=ReviewStatus.ACTIVE
            ).first()

            if review:
                return {
                    'id': str(review.id),
                    'rating': review.rating,
                    'text': review.text[:150] if review.text else '',
                    'created_at': review.created_at.isoformat(),
                }
        except Exception:
            pass
        return None


class NurseReviewHistorySerializer(serializers.Serializer):
    """Serializer for nurse's review history (completed services)."""
    id = serializers.IntegerField(read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    patient_name = serializers.SerializerMethodField()
    completed_at = serializers.DateTimeField(read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    review = serializers.SerializerMethodField()

    def get_patient_name(self, obj):
        """Get anonymized patient name."""
        name = obj.get_patient_display_name()
        if name and len(name) > 2:
            return f"{name[0]}***{name[-1]}"
        return "Patient"

    def get_review(self, obj):
        """Get review for this service if exists."""
        try:
            from reviews.models import Review, ReviewStatus
            from django.contrib.contenttypes.models import ContentType

            # Look for review with this request as context
            request_ct = ContentType.objects.get_for_model(obj)
            review = Review.objects.filter(
                context_content_type=request_ct,
                context_object_id=str(obj.id),
                status=ReviewStatus.ACTIVE
            ).first()

            if review:
                return {
                    'rating': review.rating,
                    'text': review.text[:100] if review.text else '',
                }
        except Exception:
            pass
        return None
