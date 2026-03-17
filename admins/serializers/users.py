"""
Admin serializers for user management.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.enums import UserRole

User = get_user_model()


class AdminUserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the user list endpoint."""

    is_provider = serializers.SerializerMethodField()
    is_patient = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'account_status',
            'is_active',
            'is_provider',
            'is_patient',
            'created_at',
            'last_login',
        ]
        read_only_fields = fields

    def get_is_provider(self, obj):
        return obj.role == UserRole.PROVIDER

    def get_is_patient(self, obj):
        return obj.role == UserRole.PATIENT


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Full user detail including provider/patient summary and login stats."""

    full_name = serializers.CharField(source='get_full_name', read_only=True)
    provider_summary = serializers.SerializerMethodField()
    patient_summary = serializers.SerializerMethodField()
    admin_sub_role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'account_status',
            'is_active',
            'is_staff',
            'email_verified',
            'email_verified_at',
            'profile_completed',
            'profile_completion_percentage',
            'failed_login_attempts',
            'locked_until',
            'last_login',
            'last_login_ip',
            'created_at',
            'updated_at',
            'provider_summary',
            'patient_summary',
            'admin_sub_role',
        ]
        read_only_fields = fields

    def get_provider_summary(self, obj):
        if obj.role != UserRole.PROVIDER:
            return None
        try:
            p = obj.provider_profile
            return {
                'id': p.id,
                'provider_type': p.provider_type,
                'status': p.status,
                'approved_at': p.approved_at,
                'created_at': p.created_at,
            }
        except Exception:
            return None

    def get_patient_summary(self, obj):
        if obj.role != UserRole.PATIENT:
            return None
        try:
            rec = obj.patient_record
            return {
                'id': rec.id,
                'patient_unique_id': rec.patient_unique_id,
                'full_name': rec.full_name,
            }
        except Exception:
            return None

    def get_admin_sub_role(self, obj):
        try:
            return obj.admin_profile.sub_role
        except Exception:
            return None


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Editable fields an admin can change on a user."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'email_verified']

    def validate_email_verified(self, value):
        """Allow admins to manually mark email as verified."""
        return value


class AdminUserSuspendSerializer(serializers.Serializer):
    """Optional reason when suspending or deactivating a user."""
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        default='',
    )
