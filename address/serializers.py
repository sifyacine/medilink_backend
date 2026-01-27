"""
Address serializers.
"""
from rest_framework import serializers
from address.models import Address
from django.contrib.contenttypes.models import ContentType


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model."""
    content_type_name = serializers.CharField(
        source='content_type.model',
        read_only=True
    )
    
    class Meta:
        model = Address
        fields = [
            'id',
            'content_type',
            'content_type_name',
            'object_id',
            'street',
            'city',
            'state',
            'zip_code',
            'country',
            'latitude',
            'longitude',
            'is_primary',
            'address_type',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            # These are normally set automatically in the view when creating
            # an address for the current user/provider, so they must be
            # optional from the client side.
            'content_type': {'required': False, 'allow_null': True},
            'object_id': {'required': False, 'allow_null': True},
        }
    
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
        
        return attrs
