"""
Provider serializers.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from providers.models.provider import Provider
from common.enums import ProviderStatus, ProviderType
from reviews.models import ReviewAggregate
from social_media.models import SocialMediaLink
from social_media.serializers import SocialMediaLinkSerializer
from address.models import Address
from address.serializers import AddressSerializer


class ProviderPublicListSerializer(serializers.ModelSerializer):
    """
    Public list serializer for browsing providers.
    Shows summary information suitable for list/search views.
    
    Used in: GET /api/provider/public/
    """
    provider_type_display = serializers.CharField(
        source='get_provider_type_display',
        read_only=True
    )
    
    # Provider identity (varies by type)
    name = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    
    # Summary info
    specialty = serializers.SerializerMethodField()  # Primary specialty for doctors
    years_of_experience = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    is_home_service_available = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()  # Average rating + count
    primary_address = serializers.SerializerMethodField()
    
    # Location summary
    city = serializers.SerializerMethodField()
    
    class Meta:
        model = Provider
        fields = [
            'id',
            'provider_type',
            'provider_type_display',
            'name',
            'profile_image',
            'specialty',
            'years_of_experience',
            'is_available',
            'is_home_service_available',
            'rating',
            'city',
            'primary_address',
            'created_at',
        ]
    
    def get_name(self, obj):
        """Get display name based on provider type."""
        if obj.provider_type == ProviderType.DOCTOR:
            try:
                doctor = obj.doctor_profile
                return f"Dr. {doctor.first_name} {doctor.last_name}"
            except:
                pass
        elif obj.provider_type == ProviderType.NURSE:
            try:
                nurse = obj.nurse_profile
                return f"{nurse.first_name} {nurse.last_name}"
            except:
                pass
        elif obj.provider_type == ProviderType.CLINIC:
            try:
                return obj.clinic_profile.clinic_name
            except:
                pass
        elif obj.provider_type == ProviderType.LABORATORY:
            try:
                return obj.laboratory_profile.lab_name
            except:
                pass
        elif obj.provider_type == ProviderType.SELLER:
            try:
                return obj.seller_profile.business_name
            except:
                pass
        elif obj.provider_type == ProviderType.VTC:
            try:
                return obj.vtc_profile.company_name
            except:
                pass
        return "Unknown Provider"
    
    def get_profile_image(self, obj):
        """Get profile image URL."""
        request = self.context.get('request')
        image = None
        
        if obj.provider_type == ProviderType.DOCTOR:
            try:
                image = obj.doctor_profile.profile_image
            except:
                pass
        elif obj.provider_type == ProviderType.NURSE:
            try:
                image = obj.nurse_profile.profile_image
            except:
                pass
        elif obj.provider_type == ProviderType.CLINIC:
            try:
                image = obj.clinic_profile.logo
            except:
                pass
        
        if image and request:
            return request.build_absolute_uri(image.url)
        elif image:
            return image.url
        return None
    
    def get_specialty(self, obj):
        """Get primary specialty for doctors."""
        if obj.provider_type == ProviderType.DOCTOR:
            try:
                from specialties.models import DoctorSpecialty
                primary = DoctorSpecialty.objects.filter(
                    doctor=obj.doctor_profile,
                    is_primary=True
                ).select_related('specialty').first()
                if primary:
                    return {
                        'id': primary.specialty.id,
                        'title': primary.specialty.title,
                        'slug': primary.specialty.slug,
                    }
                # Fallback to first specialty
                first = DoctorSpecialty.objects.filter(
                    doctor=obj.doctor_profile
                ).select_related('specialty').first()
                if first:
                    return {
                        'id': first.specialty.id,
                        'title': first.specialty.title,
                        'slug': first.specialty.slug,
                    }
            except:
                pass
        return None
    
    def get_years_of_experience(self, obj):
        """Get years of experience."""
        if obj.provider_type == ProviderType.DOCTOR:
            try:
                return obj.doctor_profile.years_of_experience
            except:
                pass
        elif obj.provider_type == ProviderType.NURSE:
            try:
                return obj.nurse_profile.years_of_experience
            except:
                pass
        return None
    
    def get_is_available(self, obj):
        """Get availability status."""
        try:
            if obj.provider_type == ProviderType.DOCTOR:
                return obj.doctor_profile.is_available
            elif obj.provider_type == ProviderType.NURSE:
                return obj.nurse_profile.is_available
            elif obj.provider_type == ProviderType.CLINIC:
                return obj.clinic_profile.is_available
            elif obj.provider_type == ProviderType.LABORATORY:
                return obj.laboratory_profile.is_available
        except:
            pass
        return True
    
    def get_is_home_service_available(self, obj):
        """Get home service availability."""
        try:
            if obj.provider_type == ProviderType.DOCTOR:
                return obj.doctor_profile.is_home_service_available
            elif obj.provider_type == ProviderType.NURSE:
                return obj.nurse_profile.is_home_service_available
        except:
            pass
        return False
    
    def get_rating(self, obj):
        """Get average rating and count for this provider."""
        try:
            ct = ContentType.objects.get_for_model(Provider)
            aggregate = ReviewAggregate.objects.filter(
                content_type=ct,
                object_id=str(obj.id)
            ).first()
            if not aggregate:
                return None
            return {
                'average': float(aggregate.average_rating),
                'count': aggregate.review_count,
            }
        except Exception:
            return None
    
    def get_city(self, obj):
        """Get primary city from address."""
        try:
            ct = ContentType.objects.get_for_model(Provider)
            addr = Address.objects.filter(
                content_type=ct,
                object_id=obj.id
            ).order_by('-is_primary', 'created_at').first()
            return addr.city if addr else None
        except Exception:
            return None

    def get_primary_address(self, obj):
        """Return the provider's primary address (full details) for quick access."""
        try:
            ct = ContentType.objects.get_for_model(Provider)
            addr = Address.objects.filter(
                content_type=ct,
                object_id=obj.id
            ).order_by('-is_primary', 'created_at').first()
            return AddressSerializer(addr).data if addr else None
        except Exception:
            return None


class ProviderPublicDetailSerializer(serializers.ModelSerializer):
    """
    Detailed public serializer for viewing a single provider.
    Shows complete public information for the provider detail page.
    
    Used in: GET /api/provider/public/{id}/
    """
    provider_type_display = serializers.CharField(
        source='get_provider_type_display',
        read_only=True
    )
    
    # Full profile data based on provider type
    doctor = serializers.SerializerMethodField()
    nurse = serializers.SerializerMethodField()
    clinic = serializers.SerializerMethodField()
    laboratory = serializers.SerializerMethodField()
    
    # Common computed fields
    name = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    
    class Meta:
        model = Provider
        fields = [
            'id',
            'provider_type',
            'provider_type_display',
            'name',
            'doctor',
            'nurse',
            'clinic',
            'laboratory',
            'services',
            'addresses',
            'rating',
            'social_links',
            'created_at',
        ]
    
    def get_name(self, obj):
        """Get display name based on provider type."""
        if obj.provider_type == ProviderType.DOCTOR:
            try:
                doctor = obj.doctor_profile
                return f"Dr. {doctor.first_name} {doctor.last_name}"
            except:
                pass
        elif obj.provider_type == ProviderType.NURSE:
            try:
                nurse = obj.nurse_profile
                return f"{nurse.first_name} {nurse.last_name}"
            except:
                pass
        elif obj.provider_type == ProviderType.CLINIC:
            try:
                return obj.clinic_profile.clinic_name
            except:
                pass
        elif obj.provider_type == ProviderType.LABORATORY:
            try:
                return obj.laboratory_profile.lab_name
            except:
                pass
        return "Unknown Provider"
    
    def get_doctor(self, obj):
        """Get doctor profile if provider is a doctor."""
        if obj.provider_type != ProviderType.DOCTOR:
            return None
        try:
            from providers.serializers.doctor import DoctorPublicSerializer
            return DoctorPublicSerializer(obj.doctor_profile, context=self.context).data
        except:
            return None
    
    def get_nurse(self, obj):
        """Get nurse profile if provider is a nurse."""
        if obj.provider_type != ProviderType.NURSE:
            return None
        try:
            from providers.serializers.nurse import NursePublicSerializer
            return NursePublicSerializer(obj.nurse_profile, context=self.context).data
        except:
            return None
    
    def get_clinic(self, obj):
        """Get clinic profile if provider is a clinic."""
        if obj.provider_type != ProviderType.CLINIC:
            return None
        try:
            from providers.serializers.clinic import ClinicPublicSerializer
            return ClinicPublicSerializer(obj.clinic_profile, context=self.context).data
        except:
            return None
    
    def get_laboratory(self, obj):
        """Get laboratory profile if provider is a laboratory."""
        if obj.provider_type != ProviderType.LABORATORY:
            return None
        try:
            from providers.serializers.laboratory import LaboratoryPublicSerializer
            return LaboratoryPublicSerializer(obj.laboratory_profile, context=self.context).data
        except:
            return None
    
    def get_services(self, obj):
        """Get services offered by the provider."""
        try:
            if obj.provider_type == ProviderType.DOCTOR:
                from services.models import DoctorService
                doctor_services = DoctorService.objects.filter(
                    doctor=obj.doctor_profile,
                    is_available=True
                ).select_related('service')
                return [{
                    'id': ds.service.id,
                    'title': ds.service.title,
                    'description': ds.service.description,
                    'price': str(ds.custom_price or ds.service.price),
                    'duration_minutes': ds.service.duration_minutes,
                    'is_home_service': ds.service.is_home_service,
                } for ds in doctor_services]
            elif obj.provider_type == ProviderType.NURSE:
                from services.models import NurseService
                nurse_services = NurseService.objects.filter(
                    nurse=obj.nurse_profile,
                    is_available=True
                ).select_related('service')
                return [{
                    'id': ns.service.id,
                    'title': ns.service.title,
                    'description': ns.service.description,
                    'price': str(ns.custom_price or ns.service.price),
                    'duration_minutes': ns.service.duration_minutes,
                    'is_home_service': ns.service.is_home_service,
                } for ns in nurse_services]
        except:
            pass
        return []
    
    def get_addresses(self, obj):
        """Get provider addresses."""
        try:
            from django.contrib.contenttypes.models import ContentType
            from address.models import Address
            from address.serializers import AddressSerializer
            
            provider_ct = ContentType.objects.get_for_model(Provider)
            addresses = Address.objects.filter(
                content_type=provider_ct,
                object_id=obj.id,
            )
            return AddressSerializer(addresses, many=True).data
        except:
            return []

    def get_rating(self, obj):
        """Return rating aggregate with distribution."""
        try:
            ct = ContentType.objects.get_for_model(Provider)
            aggregate = ReviewAggregate.objects.filter(
                content_type=ct,
                object_id=str(obj.id)
            ).first()
            if not aggregate:
                return None
            return {
                'average': float(aggregate.average_rating),
                'count': aggregate.review_count,
                'distribution': {
                    1: aggregate.rating_1_count,
                    2: aggregate.rating_2_count,
                    3: aggregate.rating_3_count,
                    4: aggregate.rating_4_count,
                    5: aggregate.rating_5_count,
                },
            }
        except Exception:
            return None

    def get_social_links(self, obj):
        """Return visible social links for this provider."""
        try:
            ct = ContentType.objects.get_for_model(Provider)
            links = SocialMediaLink.objects.filter(
                content_type=ct,
                object_id=obj.id,
                is_visible=True,
            ).order_by('display_order', 'platform')
            return SocialMediaLinkSerializer(links, many=True).data
        except Exception:
            return []


class ProviderPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for provider profiles (read-only, safe fields).
    
    SECURITY CONTRACT:
    This serializer is used for public endpoints accessible to unauthenticated users.
    It explicitly excludes sensitive information:
    - No email addresses (removed for privacy)
    - No internal IDs that could be used for enumeration
    - No verification metadata (verified_by, verified_at)
    - No refusal reasons
    - Only safe, public-facing information
    
    Fields exposed:
    - provider_type: Type of provider (safe)
    - status: Verification status (safe - only VERIFIED shown anyway)
    - created_at: Account creation date (safe)
    """
    provider_type_display = serializers.CharField(
        source='get_provider_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    # NOTE: Email removed from public serializer for privacy
    # If needed, use a public identifier instead
    
    class Meta:
        model = Provider
        fields = [
            'id',  # Public ID is acceptable for public profiles
            'provider_type',
            'provider_type_display',
            'status',
            'status_display',
            'created_at',
        ]
        read_only_fields = ['id', 'provider_type', 'status', 'created_at']


class ProviderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for provider (for verified providers only)."""
    email = serializers.EmailField(source='user.email', read_only=True)
    provider_type_display = serializers.CharField(
        source='get_provider_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = Provider
        fields = [
            'id',
            'email',
            'provider_type',
            'provider_type_display',
            'status',
            'status_display',
            'refusal_reason',
            'verified_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'provider_type',
            'status',
            'refusal_reason',
            'verified_at',
            'created_at',
            'updated_at',
        ]
