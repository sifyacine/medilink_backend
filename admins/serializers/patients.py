"""
Admin serializers for patient record management.
"""
from rest_framework import serializers

from patients.models import PatientRecord


class AdminPatientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the admin patient list."""

    full_name = serializers.CharField(read_only=True)
    linked_user_email = serializers.SerializerMethodField()
    is_linked = serializers.BooleanField(read_only=True)

    class Meta:
        model = PatientRecord
        fields = [
            'id',
            'patient_unique_id',
            'full_name',
            'linked_user_email',
            'is_linked',
            'city',
            'country',
            'blood_type',
            'is_active',
            'is_deleted',
            'created_at',
        ]
        read_only_fields = fields

    def get_linked_user_email(self, obj):
        return obj.linked_user.email if obj.linked_user else None


class AdminPatientDetailSerializer(serializers.ModelSerializer):
    """Full patient record detail for admin view."""

    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    is_linked = serializers.BooleanField(read_only=True)
    linked_user_email = serializers.SerializerMethodField()
    linked_user_status = serializers.SerializerMethodField()
    access_count = serializers.SerializerMethodField()
    created_by_provider_email = serializers.SerializerMethodField()

    class Meta:
        model = PatientRecord
        fields = [
            'id',
            'patient_unique_id',
            'full_name',
            'first_name',
            'last_name',
            'date_of_birth',
            'age',
            'gender',
            'phone_number',
            'email',
            'blood_type',
            'known_allergies',
            'chronic_conditions',
            'current_medications',
            'national_id',
            'address',
            'city',
            'state',
            'country',
            'emergency_contact_name',
            'emergency_contact_phone',
            'is_linked',
            'linked_user_email',
            'linked_user_status',
            'access_count',
            'is_active',
            'is_deleted',
            'deleted_at',
            'notes',
            'created_by_provider_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_linked_user_email(self, obj):
        return obj.linked_user.email if obj.linked_user else None

    def get_linked_user_status(self, obj):
        if obj.linked_user:
            return obj.linked_user.account_status
        return None

    def get_access_count(self, obj):
        return obj.provider_access.count()

    def get_created_by_provider_email(self, obj):
        if obj.created_by_provider:
            return obj.created_by_provider.user.email
        return None
