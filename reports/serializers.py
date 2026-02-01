"""Serializers for the reports app."""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from reports.models import Report, ReportAggregate, UserBan, ReportReason


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model."""
    reporter_email = serializers.EmailField(source='reporter.email', read_only=True)
    reported_type = serializers.SerializerMethodField()
    reported_user_email = serializers.EmailField(
        source='reported_user.email', read_only=True, allow_null=True
    )
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reporter_email',
            'reported_content_type', 'reported_object_id', 'reported_type',
            'reported_user', 'reported_user_email',
            'reason', 'description', 'evidence_image', 'evidence_file',
            'status', 'priority',
            'reviewed_by', 'reviewed_at', 'action_taken', 'action_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reporter', 'status', 'priority',
            'reviewed_by', 'reviewed_at', 'action_taken', 'action_notes',
            'created_at', 'updated_at'
        ]
    
    def get_reported_type(self, obj):
        """Return the model name of the reported object."""
        return obj.reported_content_type.model


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reports with simplified target identification."""
    target_type = serializers.CharField(
        write_only=True,
        help_text='Model name: provider, user, review, etc.'
    )
    target_id = serializers.CharField(
        write_only=True,
        help_text='ID of the target object'
    )
    target_user_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text='ID of the user being reported (if applicable)'
    )
    
    class Meta:
        model = Report
        fields = [
            'id', 'target_type', 'target_id', 'target_user_id',
            'reason', 'description', 'evidence_image', 'evidence_file',
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
    
    def validate_reason(self, value):
        """Validate reason is a valid choice."""
        valid_reasons = [choice[0] for choice in ReportReason.choices]
        if value not in valid_reasons:
            raise serializers.ValidationError(f"Invalid reason: {value}")
        return value
    
    def create(self, validated_data):
        """Create a report with proper content type handling."""
        from accounts.models import User
        
        target_type = validated_data.pop('target_type')
        target_id = validated_data.pop('target_id')
        target_user_id = validated_data.pop('target_user_id', None)
        
        reported_content_type = ContentType.objects.get(model=target_type)
        
        reported_user = None
        if target_user_id:
            try:
                reported_user = User.objects.get(id=target_user_id)
            except User.DoesNotExist:
                pass
        
        report = Report.objects.create(
            reporter=self.context['request'].user,
            reported_content_type=reported_content_type,
            reported_object_id=target_id,
            reported_user=reported_user,
            **validated_data
        )
        
        return report


class ReportActionSerializer(serializers.Serializer):
    """Serializer for taking action on a report."""
    action = serializers.ChoiceField(
        choices=['dismiss', 'warn', 'hide', 'suspend', 'ban', 'escalate'],
        help_text='Action to take'
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Notes about the action'
    )
    ban_duration_days = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text='For suspend/ban actions: duration in days (omit for permanent)'
    )


class ReportAggregateSerializer(serializers.ModelSerializer):
    """Serializer for ReportAggregate model."""
    entity_type = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportAggregate
        fields = [
            'id', 'content_type', 'object_id', 'entity_type',
            'total_reports', 'pending_reports', 'actioned_reports',
            'last_reported_at', 'updated_at'
        ]
        read_only_fields = '__all__'
    
    def get_entity_type(self, obj):
        """Return the model name."""
        return obj.content_type.model


class UserBanSerializer(serializers.ModelSerializer):
    """Serializer for UserBan model."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    banned_by_email = serializers.EmailField(
        source='banned_by.email', read_only=True, allow_null=True
    )
    
    class Meta:
        model = UserBan
        fields = [
            'id', 'user', 'user_email',
            'reason', 'is_permanent', 'expires_at',
            'banned_by', 'banned_by_email',
            'is_active', 'lifted_at', 'lifted_by', 'lift_reason',
            'created_at'
        ]
        read_only_fields = [
            'id', 'banned_by', 'is_active',
            'lifted_at', 'lifted_by', 'lift_reason', 'created_at'
        ]


class UserBanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user bans."""
    
    class Meta:
        model = UserBan
        fields = [
            'user', 'reason', 'is_permanent', 'expires_at', 'related_report'
        ]
    
    def validate(self, data):
        """Ensure proper ban configuration."""
        if not data.get('is_permanent') and not data.get('expires_at'):
            raise serializers.ValidationError(
                'Either set is_permanent=True or provide expires_at for temporary ban.'
            )
        return data
    
    def create(self, validated_data):
        """Create ban and optionally update user status."""
        ban = UserBan.objects.create(
            banned_by=self.context['request'].user,
            **validated_data
        )
        
        # Update user account status
        user = validated_data['user']
        from common.enums import UserAccountStatus
        user.account_status = UserAccountStatus.SUSPENDED
        user.save(update_fields=['account_status'])
        
        return ban


class ReportListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing reports."""
    reporter_email = serializers.EmailField(source='reporter.email', read_only=True)
    reported_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter_email', 'reported_type', 'reported_object_id',
            'reason', 'status', 'priority', 'created_at'
        ]
    
    def get_reported_type(self, obj):
        return obj.reported_content_type.model
