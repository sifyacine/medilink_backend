"""
Provider Status serializers.
"""
from rest_framework import serializers

from providers.models.provider import Provider


class ProviderStatusSerializer(serializers.ModelSerializer):
    """Serializer for provider status information."""
    
    class Meta:
        model = Provider
        fields = [
            'status',
            'refusal_reason',
            'approved_at',
            'verified_at',  # Legacy field
        ]
        read_only_fields = ['status', 'refusal_reason', 'approved_at', 'verified_at']
