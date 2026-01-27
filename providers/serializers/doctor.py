"""
Doctor serializers.
"""
from rest_framework import serializers
from providers.models.doctor import Doctor, DoctorCertification
from providers.serializers.status import ProviderStatusSerializer


class DoctorSerializer(serializers.ModelSerializer):
    """Serializer for Doctor profile."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    email = serializers.EmailField(source='provider.user.email', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    
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
            'license_number',
            'years_of_experience',
            'biography',
            'degree_document',
            'is_verified',
            'is_available',
            'is_home_service_available',
            'provider_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']


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
