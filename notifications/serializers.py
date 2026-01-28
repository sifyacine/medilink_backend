"""
Serializers for the Notifications app.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from .models import (
    Notification,
    DeviceToken,
    NotificationPreference,
    NotificationType,
    NotificationCategory,
    NotificationPriority,
)


class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer for listing notifications."""
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'image_url',
            'notification_type',
            'notification_type_display',
            'category',
            'category_display',
            'priority',
            'priority_display',
            'is_read',
            'read_at',
            'action_url',
            'created_at',
            'time_ago',
        ]
        read_only_fields = fields
    
    def get_time_ago(self, obj):
        """Calculate human-readable time ago."""
        from django.utils import timezone
        from datetime import timedelta
        
        diff = timezone.now() - obj.created_at
        
        if diff < timedelta(minutes=1):
            return 'Just now'
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f'{minutes}m ago'
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f'{hours}h ago'
        elif diff < timedelta(days=7):
            days = diff.days
            return f'{days}d ago'
        else:
            return obj.created_at.strftime('%b %d, %Y')


class NotificationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single notification."""
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    related_object_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'image_url',
            'notification_type',
            'notification_type_display',
            'category',
            'category_display',
            'priority',
            'priority_display',
            'is_read',
            'read_at',
            'push_sent',
            'push_sent_at',
            'action_url',
            'data',
            'expires_at',
            'related_object_info',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_related_object_info(self, obj):
        """Get information about the related object."""
        if obj.related_content_type and obj.related_object_id:
            return {
                'content_type': obj.related_content_type.model,
                'object_id': obj.related_object_id,
            }
        return None


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications (admin use)."""
    recipient_id = serializers.UUIDField(write_only=True)
    related_content_type = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = Notification
        fields = [
            'recipient_id',
            'title',
            'message',
            'image_url',
            'notification_type',
            'category',
            'priority',
            'related_content_type',
            'related_object_id',
            'action_url',
            'data',
            'expires_at',
        ]
    
    def validate_related_content_type(self, value):
        """Convert content type string to ContentType object."""
        if not value:
            return None
        try:
            app_label, model = value.split('.')
            return ContentType.objects.get(app_label=app_label, model=model)
        except (ValueError, ContentType.DoesNotExist):
            raise serializers.ValidationError(
                'Invalid content type. Use format: app_label.model'
            )
    
    def create(self, validated_data):
        from accounts.models import User
        
        recipient_id = validated_data.pop('recipient_id')
        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({'recipient_id': 'User not found.'})
        
        validated_data['recipient'] = recipient
        return super().create(validated_data)


class BulkNotificationSerializer(serializers.Serializer):
    """Serializer for sending bulk notifications."""
    recipient_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=1000,
        help_text='List of user IDs to notify'
    )
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    image_url = serializers.URLField(required=False, allow_null=True)
    notification_type = serializers.ChoiceField(
        choices=NotificationType.choices,
        default=NotificationType.GENERAL
    )
    category = serializers.ChoiceField(
        choices=NotificationCategory.choices,
        default=NotificationCategory.SYSTEM
    )
    priority = serializers.ChoiceField(
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL
    )
    action_url = serializers.CharField(required=False, allow_blank=True)
    data = serializers.JSONField(required=False, default=dict)
    send_push = serializers.BooleanField(default=True)


class MarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text='List of notification IDs to mark as read. If empty, marks all as read.'
    )


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Serializer for device tokens."""
    
    class Meta:
        model = DeviceToken
        fields = [
            'id',
            'token',
            'device_type',
            'device_name',
            'device_id',
            'app_version',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']
    
    def validate_token(self, value):
        """Validate token uniqueness for this user."""
        user = self.context['request'].user
        existing = DeviceToken.objects.filter(token=value).exclude(user=user).first()
        if existing:
            # Token belongs to another user, update ownership
            existing.user = user
            existing.is_active = True
            existing.failure_count = 0
            existing.save()
            raise serializers.ValidationError('Token transferred from another device.')
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        token = validated_data.get('token')
        
        # Update existing token or create new
        device_token, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'user': user,
                'device_type': validated_data.get('device_type'),
                'device_name': validated_data.get('device_name', ''),
                'device_id': validated_data.get('device_id', ''),
                'app_version': validated_data.get('app_version', ''),
                'is_active': True,
                'failure_count': 0,
            }
        )
        return device_token


class DeviceTokenRegisterSerializer(serializers.Serializer):
    """Simple serializer for registering a device token."""
    token = serializers.CharField(max_length=500)
    device_type = serializers.ChoiceField(choices=DeviceToken.DEVICE_TYPES)
    device_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    device_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    app_version = serializers.CharField(max_length=50, required=False, allow_blank=True)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'push_enabled',
            'push_appointments',
            'push_messages',
            'push_reminders',
            'push_promotions',
            'push_system',
            'email_enabled',
            'email_appointments',
            'email_reminders',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
            'updated_at',
        ]
        read_only_fields = ['updated_at']
    
    def validate(self, data):
        """Validate quiet hours configuration."""
        quiet_enabled = data.get('quiet_hours_enabled', False)
        quiet_start = data.get('quiet_hours_start')
        quiet_end = data.get('quiet_hours_end')
        
        if quiet_enabled and (not quiet_start or not quiet_end):
            raise serializers.ValidationError({
                'quiet_hours': 'Start and end times are required when quiet hours are enabled.'
            })
        
        return data


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics."""
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    by_category = serializers.DictField()
    by_priority = serializers.DictField()
