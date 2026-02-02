"""
User serializers for account management.
"""
from rest_framework import serializers

from accounts.models import User
from common.enums import UserRole


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'role',
            'first_name',
            'last_name',
            'full_name',
            'phone_number',
            'is_active',
            'email_verified',
            'profile_completed',
            'profile_completion_percentage',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'full_name']
    
    def get_full_name(self, obj):
        """Return full name from model method."""
        return obj.get_full_name()


class UserPublicSerializer(serializers.ModelSerializer):
    """Public serializer for user information (limited fields)."""
    
    class Meta:
        model = User
        fields = ['id', 'email']
        read_only_fields = ['id', 'email']
