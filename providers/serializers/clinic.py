"""
Clinic serializers.
"""
from rest_framework import serializers
from providers.models.clinic import Clinic
from providers.serializers.status import ProviderStatusSerializer


class ClinicSerializer(serializers.ModelSerializer):
    """Serializer for Clinic profile."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    email = serializers.EmailField(source='provider.user.email', read_only=True)
    
    class Meta:
        model = Clinic
        fields = [
            'id',
            'email',
            'clinic_name',
            'license_number',
            'logo',
            'phone_number',
            'email',
            'website',
            'description',
            'number_of_beds',
            'has_emergency_services',
            'is_24_hours',
            'outpatient_capacity_per_day',
            'license_document',
            'is_verified',
            'is_available',
            'provider_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']


class ClinicStatusSerializer(serializers.ModelSerializer):
    """Serializer for clinic status information."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    
    class Meta:
        model = Clinic
        fields = [
            'clinic_name',
            'has_emergency_services',
            'is_24_hours',
            'provider_status',
            'is_verified',
            'is_available',
        ]
        read_only_fields = ['clinic_name', 'has_emergency_services', 'is_24_hours', 'provider_status', 'is_verified', 'is_available']


class ClinicCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Clinic profile."""
    
    class Meta:
        model = Clinic
        fields = [
            'clinic_name',
            'license_number',
            'logo',
            'phone_number',
            'email',
            'website',
            'description',
            'number_of_beds',
            'has_emergency_services',
            'is_24_hours',
            'outpatient_capacity_per_day',
            'license_document',
        ]
