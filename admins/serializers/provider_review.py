"""
Admin serializers for provider verification workflow.
"""
from rest_framework import serializers

from providers.models import Provider
from providers.serializers.provider import ProviderPublicSerializer


class ProviderListSerializer(serializers.ModelSerializer):
    """Serializer for listing providers in admin panel."""
    email = serializers.EmailField(source='user.email', read_only=True)
    provider_type_display = serializers.CharField(
        source='get_provider_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    verified_by_email = serializers.EmailField(
        source='verified_by.email',
        read_only=True,
        allow_null=True
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
            'verified_by_email',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'provider_type',
            'status',
            'refusal_reason',
            'verified_at',
            'verified_by_email',
            'created_at',
        ]


class ProviderRefuseSerializer(serializers.Serializer):
    """Serializer for refusing a provider (requires reason)."""
    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        min_length=10,
        help_text='Reason for refusing the provider (minimum 10 characters)'
    )
    
    def validate_reason(self, value):
        """Validate that reason is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError('Refusal reason cannot be empty.')
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Refusal reason must be at least 10 characters.')
        return value.strip()
