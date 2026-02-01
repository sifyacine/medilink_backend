"""Serializers for the reviews app."""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from reviews.models import Review, ReviewAggregate, ReviewHelpful, ReviewStatus


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    reviewed_type = serializers.SerializerMethodField()
    has_response = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'reviewer_email',
            'reviewed_content_type', 'reviewed_object_id', 'reviewed_type',
            'context_content_type', 'context_object_id',
            'rating', 'title', 'text', 'image',
            'status', 'response', 'response_at', 'response_by',
            'helpful_count', 'created_at', 'updated_at',
            'has_response'
        ]
        read_only_fields = [
            'id', 'reviewer', 'status', 'response', 'response_at',
            'response_by', 'helpful_count', 'created_at', 'updated_at'
        ]
    
    def get_reviewed_type(self, obj):
        """Return the model name of the reviewed object."""
        return obj.reviewed_content_type.model
    
    def get_has_response(self, obj):
        """Check if the review has a response."""
        return bool(obj.response)


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews with simplified target identification."""
    target_type = serializers.CharField(
        write_only=True,
        help_text='Model name: provider, doctor, nurse, user, clinic, etc.'
    )
    target_id = serializers.CharField(
        write_only=True,
        help_text='ID of the target object'
    )
    context_type = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Model name for context: nurseservicerequest, appointment, etc.'
    )
    context_id = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='ID of the context object'
    )
    
    class Meta:
        model = Review
        fields = [
            'id', 'target_type', 'target_id',
            'context_type', 'context_id',
            'rating', 'title', 'text', 'image',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_target_type(self, value):
        """Validate the target type exists as a model."""
        try:
            ContentType.objects.get(model=value.lower())
            return value.lower()
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid target type: {value}")
    
    def validate_context_type(self, value):
        """Validate the context type exists as a model."""
        if not value:
            return value
        try:
            ContentType.objects.get(model=value.lower())
            return value.lower()
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid context type: {value}")
    
    def validate(self, data):
        """Validate the complete data set."""
        # Ensure context is complete (both or neither)
        context_type = data.get('context_type')
        context_id = data.get('context_id')
        
        if bool(context_type) != bool(context_id):
            raise serializers.ValidationError(
                'Both context_type and context_id must be provided together.'
            )
        
        return data
    
    def create(self, validated_data):
        """Create a review with proper content type handling."""
        # Extract and remove custom fields
        target_type = validated_data.pop('target_type')
        target_id = validated_data.pop('target_id')
        context_type = validated_data.pop('context_type', None)
        context_id = validated_data.pop('context_id', None)
        
        # Get content types
        reviewed_content_type = ContentType.objects.get(model=target_type)
        
        context_content_type = None
        if context_type:
            context_content_type = ContentType.objects.get(model=context_type)
        
        # Create review
        review = Review.objects.create(
            reviewer=self.context['request'].user,
            reviewed_content_type=reviewed_content_type,
            reviewed_object_id=target_id,
            context_content_type=context_content_type,
            context_object_id=context_id,
            **validated_data
        )
        
        return review


class ReviewResponseSerializer(serializers.Serializer):
    """Serializer for adding a response to a review."""
    response = serializers.CharField(
        required=True,
        help_text='Response text'
    )
    
    def validate_response(self, value):
        """Ensure response is not empty."""
        if not value.strip():
            raise serializers.ValidationError('Response cannot be empty.')
        return value.strip()


class ReviewAggregateSerializer(serializers.ModelSerializer):
    """Serializer for ReviewAggregate model."""
    entity_type = serializers.SerializerMethodField()
    rating_distribution = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewAggregate
        fields = [
            'id', 'content_type', 'object_id', 'entity_type',
            'average_rating', 'review_count',
            'rating_distribution', 'updated_at'
        ]
        read_only_fields = '__all__'
    
    def get_entity_type(self, obj):
        """Return the model name."""
        return obj.content_type.model
    
    def get_rating_distribution(self, obj):
        """Return rating distribution as a dict."""
        return {
            1: obj.rating_1_count,
            2: obj.rating_2_count,
            3: obj.rating_3_count,
            4: obj.rating_4_count,
            5: obj.rating_5_count,
        }


class ReviewListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing reviews."""
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer_email', 'rating', 'title', 'text',
            'image', 'helpful_count', 'created_at',
            'response', 'response_at'
        ]


class BulkReviewStatsSerializer(serializers.Serializer):
    """Serializer for getting bulk review stats for multiple objects."""
    target_type = serializers.CharField(
        help_text='Model name: provider, doctor, nurse, etc.'
    )
    target_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text='List of target object IDs'
    )
    
    def validate_target_type(self, value):
        """Validate the target type exists."""
        try:
            ContentType.objects.get(model=value.lower())
            return value.lower()
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid target type: {value}")
