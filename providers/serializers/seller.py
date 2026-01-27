"""
Seller serializers.
"""
from rest_framework import serializers
from providers.models.seller import Seller
from providers.serializers.status import ProviderStatusSerializer


class SellerSerializer(serializers.ModelSerializer):
    """Serializer for Seller profile."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    email = serializers.EmailField(source='provider.user.email', read_only=True)
    
    class Meta:
        model = Seller
        fields = [
            'id',
            'email',
            'business_name',
            'tax_id',
            'business_type',
            'phone_number',
            'email',
            'website',
            'description',
            'business_license',
            'tax_certificate',
            'is_verified',
            'is_available',
            'provider_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']


class SellerStatusSerializer(serializers.ModelSerializer):
    """Serializer for seller status information."""
    provider_status = ProviderStatusSerializer(source='provider', read_only=True)
    
    class Meta:
        model = Seller
        fields = [
            'business_name',
            'provider_status',
            'is_verified',
            'is_available',
        ]
        read_only_fields = ['business_name', 'provider_status', 'is_verified', 'is_available']


class SellerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Seller profile."""
    
    class Meta:
        model = Seller
        fields = [
            'business_name',
            'tax_id',
            'business_type',
            'phone_number',
            'email',
            'website',
            'description',
            'business_license',
            'tax_certificate',
        ]
