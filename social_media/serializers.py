"""
Social media serializers.
"""
from rest_framework import serializers
from social_media.models import SocialMediaLink
from django.contrib.contenttypes.models import ContentType


class SocialMediaLinkSerializer(serializers.ModelSerializer):
    """Serializer for SocialMediaLink model."""
    platform_display = serializers.CharField(
        source='get_platform_display',
        read_only=True
    )
    content_type_name = serializers.CharField(
        source='content_type.model',
        read_only=True
    )
    
    class Meta:
        model = SocialMediaLink
        fields = [
            'id',
            'content_type',
            'content_type_name',
            'object_id',
            'platform',
            'platform_display',
            'url',
            'custom_label',
            'is_visible',
            'display_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate that content_type and object_id match a valid object."""
        content_type = attrs.get('content_type')
        object_id = attrs.get('object_id')
        
        if content_type and object_id:
            try:
                model_class = content_type.model_class()
                if model_class:
                    obj = model_class.objects.get(pk=object_id)
                    # Object exists, validation passed
                else:
                    raise serializers.ValidationError('Invalid content type.')
            except model_class.DoesNotExist:
                raise serializers.ValidationError(
                    f'Object with id {object_id} does not exist for {content_type}.'
                )
        
        # Validate custom_label for OTHER platform
        if attrs.get('platform') == 'OTHER' and not attrs.get('custom_label'):
            raise serializers.ValidationError(
                'custom_label is required when platform is OTHER.'
            )
        
        return attrs
