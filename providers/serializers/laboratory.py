"""
Laboratory serializers.
"""
from rest_framework import serializers
from providers.models.laboratory import Laboratory
from providers.serializers.status import ProviderStatusSerializer


class LaboratorySerializer(serializers.ModelSerializer):
    """Serializer for Laboratory profile."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    email = serializers.EmailField(source='provider.user.email', read_only=True)
    
    class Meta:
        model = Laboratory
        fields = [
            'id',
            'email',
            'lab_name',
            'license_number',
            'accreditation',
            'phone_number',
            'email',
            'website',
            'description',
            'license_document',
            'accreditation_document',
            'is_verified',
            'is_available',
            'provider_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']


class LaboratoryStatusSerializer(serializers.ModelSerializer):
    """Serializer for laboratory status information."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    
    class Meta:
        model = Laboratory
        fields = [
            'lab_name',
            'provider_status',
            'is_verified',
            'is_available',
        ]
        read_only_fields = ['lab_name', 'provider_status', 'is_verified', 'is_available']


class LaboratoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Laboratory profile."""
    
    class Meta:
        model = Laboratory
        fields = [
            'lab_name',
            'license_number',
            'accreditation',
            'phone_number',
            'email',
            'website',
            'description',
            'license_document',
            'accreditation_document',
        ]
