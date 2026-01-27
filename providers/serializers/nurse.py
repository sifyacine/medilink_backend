"""
Nurse serializers.
"""
from rest_framework import serializers
from providers.models.nurse import Nurse, NurseCertification
from providers.serializers.status import ProviderStatusSerializer


class NurseSerializer(serializers.ModelSerializer):
    """Serializer for Nurse profile."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    email = serializers.EmailField(source='provider.user.email', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    
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
            'provider_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']


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
