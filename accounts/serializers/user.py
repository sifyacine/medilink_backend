"""
User serializers for account management.
"""
from rest_framework import serializers

from accounts.models import User
from common.enums import UserRole


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'role',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class UserPublicSerializer(serializers.ModelSerializer):
    """Public serializer for user information (limited fields)."""
    
    class Meta:
        model = User
        fields = ['id', 'email']
        read_only_fields = ['id', 'email']
