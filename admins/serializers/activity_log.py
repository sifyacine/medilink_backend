"""
Admin serializer for AdminActivityLog.
"""
from rest_framework import serializers

from admins.models import AdminActivityLog
from common.enums import AdminActionType


class AdminActivityLogSerializer(serializers.ModelSerializer):
    """Full activity log entry with human-readable labels."""

    admin_email = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()
    content_type_label = serializers.SerializerMethodField()

    class Meta:
        model = AdminActivityLog
        fields = [
            'id',
            'admin_email',
            'action',
            'action_display',
            'content_type_label',
            'object_id',
            'object_repr',
            'ip_address',
            'extra_data',
            'created_at',
        ]
        read_only_fields = fields

    def get_admin_email(self, obj):
        return obj.admin.email if obj.admin else None

    def get_action_display(self, obj):
        try:
            return AdminActionType(obj.action).label
        except ValueError:
            return obj.action

    def get_content_type_label(self, obj):
        return obj.content_type.model if obj.content_type else None
