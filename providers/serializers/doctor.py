"""
Doctor serializers.
"""
from rest_framework import serializers
from providers.models.doctor import Doctor, DoctorCertification
from providers.serializers.status import ProviderStatusSerializer


class DoctorSpecialtyListSerializer(serializers.Serializer):
    """Lightweight serializer for doctor's specialties in profile response."""
    id = serializers.IntegerField(source='specialty.id', read_only=True)
    title = serializers.CharField(source='specialty.title', read_only=True)
    title_ar = serializers.CharField(source='specialty.title_ar', read_only=True)
    title_fr = serializers.CharField(source='specialty.title_fr', read_only=True)
    slug = serializers.CharField(source='specialty.slug', read_only=True)
    is_primary = serializers.BooleanField(read_only=True)
    years_of_experience = serializers.IntegerField(read_only=True, allow_null=True)


class DoctorServiceListSerializer(serializers.Serializer):
    """Lightweight serializer for doctor's services in profile response."""
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


class DoctorSerializer(serializers.ModelSerializer):
    """Serializer for Doctor profile."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    email = serializers.EmailField(source='provider.user.email', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    specialties = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()
    
    class Meta:
        model = Doctor
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
            'years_of_experience',
            'biography',
            'degree_document',
            'is_verified',
            'is_available',
            'is_home_service_available',
            # Consultation pricing
            'consultation_price',
            'home_visit_price',
            'online_consultation_price',
            'currency',
            'specialties',
            'services',
            'provider_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']
    
    def get_specialties(self, obj):
        """Return the doctor's specialties."""
        try:
            from specialties.models import DoctorSpecialty
            doctor_specialties = DoctorSpecialty.objects.filter(doctor=obj).select_related('specialty')
            return DoctorSpecialtyListSerializer(doctor_specialties, many=True).data
        except Exception:
            return []
    
    def get_services(self, obj):
        """Return the doctor's services."""
        try:
            from services.models import DoctorService
            doctor_services = DoctorService.objects.filter(doctor=obj).select_related('service')
            return DoctorServiceListSerializer(doctor_services, many=True).data
        except Exception:
            return []


class DoctorStatusSerializer(serializers.ModelSerializer):
    """Serializer for doctor status information."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Doctor
        fields = [
            'full_name',
            'provider_status',
            'is_verified',
            'is_available',
        ]
        read_only_fields = ['full_name', 'provider_status', 'is_verified', 'is_available']


class DoctorCertificationSerializer(serializers.ModelSerializer):
    """Serializer for Doctor Certification."""
    
    class Meta:
        model = DoctorCertification
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


class DoctorPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for Doctor profiles.
    Used for public browsing - excludes sensitive information.
    """
    full_name = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    specialties = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()
    
    class Meta:
        model = Doctor
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'gender',
            'gender_display',
            'profile_image',
            'years_of_experience',
            'biography',
            'is_available',
            'is_home_service_available',
            'specialties',
            'services',
            'created_at',
        ]
        # Exclude: license_number, degree_document, phone_number, date_of_birth
    
    def get_full_name(self, obj):
        return f"Dr. {obj.first_name} {obj.last_name}"
    
    def get_specialties(self, obj):
        """Return the doctor's specialties."""
        try:
            from specialties.models import DoctorSpecialty
            doctor_specialties = DoctorSpecialty.objects.filter(doctor=obj).select_related('specialty')
            return [{
                'id': ds.specialty.id,
                'title': ds.specialty.title,
                'title_ar': ds.specialty.title_ar,
                'title_fr': ds.specialty.title_fr,
                'slug': ds.specialty.slug,
                'is_primary': ds.is_primary,
            } for ds in doctor_specialties]
        except Exception:
            return []
    
    def get_services(self, obj):
        """Return the doctor's available services."""
        try:
            from services.models import DoctorService
            doctor_services = DoctorService.objects.filter(
                doctor=obj,
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
        except Exception:
            return []
