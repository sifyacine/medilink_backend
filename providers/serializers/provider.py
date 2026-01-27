"""
Provider serializers.
"""
from rest_framework import serializers

from providers.models.provider import Provider
from common.enums import ProviderStatus, ProviderType




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
