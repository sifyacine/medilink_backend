"""
Provider Status serializers.
"""
from rest_framework import serializers

from providers.models.provider import Provider


def _resolve_provider_type_display(provider):
    """Return provider type display without raising on invalid values."""
    provider_type = getattr(provider, "provider_type", None)

    if not provider_type:
        return None

    try:
        from common.enums import ProviderType

        if provider_type in ProviderType.values:
            return ProviderType(provider_type).label
    except Exception:
        # Fall back to the model helper if enum lookup fails for any reason.
        pass

    # Django's choices helper returns a human readable label.
    return provider.get_provider_type_display()


class ProviderStatusSerializer(serializers.ModelSerializer):
    """Serializer for provider status information."""

    provider_type = serializers.CharField(read_only=True)
    provider_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Provider
        fields = [
            'status',
            'refusal_reason',
            'approved_at',
            'verified_at',  # Legacy field
            'provider_type',
            'provider_type_display',
        ]
        read_only_fields = [
            'status',
            'refusal_reason',
            'approved_at',
            'verified_at',
            'provider_type',
            'provider_type_display',
        ]

    def get_provider_type_display(self, obj):
        """Expose a safe provider type label."""
        return _resolve_provider_type_display(obj)
