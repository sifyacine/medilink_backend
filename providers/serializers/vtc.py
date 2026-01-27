"""
VTC serializers.
"""
from rest_framework import serializers
from providers.models.vtc import VTC
from providers.serializers.status import ProviderStatusSerializer


class VTCSerializer(serializers.ModelSerializer):
    """Serializer for VTC profile."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    email = serializers.EmailField(source='provider.user.email', read_only=True)
    
    class Meta:
        model = VTC
        fields = [
            'id',
            'email',
            'company_name',
            'license_number',
            'phone_number',
            'email',
            'website',
            'fleet_size',
            'vehicle_types',
            'description',
            'transport_license',
            'insurance_certificate',
            'is_verified',
            'is_available',
            'provider_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']


class VTCStatusSerializer(serializers.ModelSerializer):
    """Serializer for VTC status information."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    
    class Meta:
        model = VTC
        fields = [
            'company_name',
            'provider_status',
            'is_verified',
            'is_available',
        ]
        read_only_fields = ['company_name', 'provider_status', 'is_verified', 'is_available']


class VTCCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a VTC profile."""
    
    class Meta:
        model = VTC
        fields = [
            'company_name',
            'license_number',
            'phone_number',
            'email',
            'website',
            'fleet_size',
            'vehicle_types',
            'description',
            'transport_license',
            'insurance_certificate',
        ]
