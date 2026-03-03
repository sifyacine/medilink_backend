"""
Nurse serializers.
"""
from rest_framework import serializers
from providers.models.nurse import Nurse, NurseCertification
from providers.serializers.status import ProviderStatusSerializer


class NurseServiceListSerializer(serializers.Serializer):
    """Lightweight serializer for nurse's services in profile response."""
    id = serializers.IntegerField(source='service.id', read_only=True)
    title = serializers.CharField(source='service.title', read_only=True)
    slug = serializers.CharField(source='service.slug', read_only=True)
    description = serializers.CharField(source='service.description', read_only=True)
    price = serializers.DecimalField(
        source='service.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    custom_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        allow_null=True
    )
    final_price = serializers.SerializerMethodField()
    duration_minutes = serializers.IntegerField(source='service.duration_minutes', read_only=True)
    is_home_service = serializers.BooleanField(source='service.is_home_service', read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    def get_final_price(self, obj):
        """Return custom_price if set, otherwise service price."""
        return obj.custom_price if obj.custom_price else obj.service.price


class NurseSerializer(serializers.ModelSerializer):
    """Serializer for Nurse profile."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    email = serializers.EmailField(source='provider.user.email', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    services = serializers.SerializerMethodField()
    
    class Meta:
        model = Nurse
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'gender',
            'gender_display',
            'date_of_birth',
            'profile_image',
            'phone_number',
            'license_number',
            'certification',
            'years_of_experience',
            'biography',
            'degree_document',
            'entrepreneur_card_front',
            'entrepreneur_card_back',
            'entrepreneur_card_pdf',
            'is_verified',
            'is_available',
            'is_home_service_available',
            'services',
            'provider_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']
    
    def get_services(self, obj):
        """Return the nurse's services."""
        try:
            from services.models import NurseService
            nurse_services = NurseService.objects.filter(nurse=obj).select_related('service')
            return NurseServiceListSerializer(nurse_services, many=True).data
        except Exception:
            return []


class NurseStatusSerializer(serializers.ModelSerializer):
    """Serializer for nurse status information."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Nurse
        fields = [
            'full_name',
            'provider_status',
            'is_verified',
            'is_available',
        ]
        read_only_fields = ['full_name', 'provider_status', 'is_verified', 'is_available']


class NurseCertificationSerializer(serializers.ModelSerializer):
    """Serializer for Nurse Certification."""
    
    class Meta:
        model = NurseCertification
        fields = [
            'id',
            'title',
            'issuing_organization',
            'issue_date',
            'expiry_date',
            'certificate_document',
            'is_verified',
            'created_at',
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']


class NursePublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for Nurse profiles.
    Used for public browsing - excludes sensitive information.
    """
    full_name = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    email = serializers.EmailField(source='provider.user.email', read_only=True)
    services = serializers.SerializerMethodField()

    class Meta:
        model = Nurse
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone_number',
            'gender',
            'gender_display',
            'profile_image',
            'certification',
            'years_of_experience',
            'biography',
            'is_available',
            'is_home_service_available',
            'services',
            'created_at',
        ]
        # Exclude: license_number, degree_document, date_of_birth, entrepreneur cards
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_services(self, obj):
        """Return the nurse's available services."""
        try:
            from services.models import NurseService
            nurse_services = NurseService.objects.filter(
                nurse=obj,
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
        except Exception:
            return []
