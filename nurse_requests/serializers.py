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
    nurse_profile_image = serializers.SerializerMethodField()
    nurse_id = serializers.IntegerField(source='nurse.id', read_only=True)
    
    class Meta:
        model = NurseOffer
        fields = [
            'id', 'nurse_id', 'nurse_name', 'nurse_rating',
            'nurse_profile_image', 'offered_price', 'status',
            'estimated_arrival_time', 'distance_km', 'notes',
            'created_at', 'responded_at'
        ]
        read_only_fields = [
            'id', 'nurse_id', 'nurse_name', 'nurse_rating',
            'nurse_profile_image', 'created_at', 'responded_at'
        ]
    
    def get_nurse_name(self, obj):
        return f"{obj.nurse.user.first_name} {obj.nurse.user.last_name}".strip()
    
    def get_nurse_rating(self, obj):
        # TODO: Implement rating system
        return 4.5  # Placeholder
    
    def get_nurse_profile_image(self, obj):
        # TODO: Return actual profile image URL
        return None


class NurseServiceRequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing requests"""
    service_name = serializers.CharField(source='service.name', read_only=True)
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
    
    class Meta:
        model = NurseServiceRequest
        fields = [
            'id', 'patient_user', 'patient_record', 'patient_name', 'service',
            'accepted_nurse', 'accepted_nurse_name',
            'base_price', 'patient_offered_price', 'final_price',
            'latitude', 'longitude', 'city', 'address_line',
            'status', 'notes', 'offers',
            'created_at', 'updated_at', 'accepted_at',
            'started_at', 'completed_at', 'cancelled_at',
            'cancellation_reason'
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
        if obj.accepted_nurse:
            return f"{obj.accepted_nurse.user.first_name} {obj.accepted_nurse.user.last_name}".strip()
        return None


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
                        f"Offered price (${value}) cannot be lower than "
                        f"base price (${service.price})"
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
            if offer.status != OfferStatus.PENDING:
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
                f"Counter offer (${value}) must be at least "
                f"${request.patient_offered_price}"
            )
        if value < request.base_price:
            raise serializers.ValidationError(
                f"Counter offer (${value}) cannot be lower than "
                f"base price (${request.base_price})"
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
    
    class Meta:
        model = NurseServiceRequest
        fields = [
            'id', 'service_id', 'service_name', 'service_description',
            'patient_name', 'patient_offered_price', 'base_price',
            'latitude', 'longitude', 'city', 'address_line',
            'status', 'created_at', 'my_offer'
        ]
        read_only_fields = fields
    
    def get_patient_name(self, obj):
        # Optionally hide full patient name for privacy
        name = obj.get_patient_display_name()
        if name and len(name) > 1:
            parts = name.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[-1][0]}."
        return name
    
    def get_my_offer(self, obj):
        """Get the current nurse's offer if exists"""
        nurse = self.context.get('nurse')
        if nurse:
            try:
                offer = obj.offers.get(nurse=nurse)
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
        """Return custom price if set, otherwise base price"""
        if obj.custom_price:
            return str(obj.custom_price)
        return str(obj.service.price)


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
