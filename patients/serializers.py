"""
Serializers for Patient Records app.
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from patients.models import PatientRecord, ProviderPatientAccess, MedicalRecordShareToken, ShareTokenAccessLog
from accounts.models import User
from providers.models.provider import Provider


class PatientRecordCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating patient records.
    Used by providers to create records for patients without accounts.
    """
    
    class Meta:
        model = PatientRecord
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'phone_number',
            'email',
            'emergency_contact_name',
            'emergency_contact_phone',
            'blood_type',
            'known_allergies',
            'chronic_conditions',
            'current_medications',
            'national_id',
            'address',
            'city',
            'state',
            'country',
            'notes',
        ]
    
    def validate_email(self, value):
        """Validate that email is not already linked to a patient record."""
        if value:
            # Check if a patient record with this email already exists and is linked
            existing = PatientRecord.objects.filter(email=value, linked_user__isnull=False).first()
            if existing:
                raise serializers.ValidationError(
                    'A patient record with this email is already linked to an account.'
                )
        return value
    
    def validate_national_id(self, value):
        """Validate that national ID is unique."""
        if value:
            existing = PatientRecord.objects.filter(national_id=value).first()
            if existing:
                raise serializers.ValidationError(
                    'A patient record with this national ID already exists.'
                )
        return value


class PatientRecordSerializer(serializers.ModelSerializer):
    """
    Full serializer for patient records (read operations).
    Includes computed fields and masked linking token.
    """
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    is_linked = serializers.BooleanField(read_only=True)
    
    # Mask the linking token for security - only show partial
    linking_token_masked = serializers.SerializerMethodField()
    
    # Created by provider name
    created_by_provider_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientRecord
        fields = [
            'id',
            'patient_unique_id',
            'first_name',
            'last_name',
            'full_name',
            'date_of_birth',
            'age',
            'gender',
            'phone_number',
            'email',
            'emergency_contact_name',
            'emergency_contact_phone',
            'blood_type',
            'known_allergies',
            'chronic_conditions',
            'current_medications',
            'national_id',
            'address',
            'city',
            'state',
            'country',
            'notes',
            'is_active',
            'is_linked',
            'linking_token_masked',
            'created_by_provider_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'patient_unique_id',
            'is_linked',
            'linking_token_masked',
            'created_by_provider_name',
            'created_at',
            'updated_at',
        ]
    
    def get_linking_token_masked(self, obj):
        """Return masked linking token for display."""
        if obj.token_used:
            return '***TOKEN_USED***'
        if obj.is_linked:
            return '***LINKED***'
        # Show first 8 and last 4 characters
        token = obj.linking_token
        if len(token) > 12:
            return f'{token[:8]}...{token[-4:]}'
        return '***'
    
    def get_created_by_provider_name(self, obj):
        """Return the name of the provider who created this record using centralized utility."""
        if obj.created_by_provider:
            from common.utils import get_provider_display_name
            return get_provider_display_name(obj.created_by_provider)
        return None


class PatientRecordUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating patient records.
    Excludes fields that shouldn't be updated after creation.
    """
    
    class Meta:
        model = PatientRecord
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'phone_number',
            'email',
            'emergency_contact_name',
            'emergency_contact_phone',
            'blood_type',
            'known_allergies',
            'chronic_conditions',
            'current_medications',
            'address',
            'city',
            'state',
            'country',
            'notes',
            'is_active',
        ]


class PatientRecordListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing patient records.
    """
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    is_linked = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PatientRecord
        fields = [
            'id',
            'patient_unique_id',
            'first_name',
            'last_name',
            'full_name',
            'date_of_birth',
            'age',
            'gender',
            'phone_number',
            'is_active',
            'is_linked',
            'created_at',
        ]


class LinkingTokenSerializer(serializers.Serializer):
    """
    Serializer for the linking token endpoint.
    Returns the full linking token (for providers to give to patients).
    """
    linking_token = serializers.CharField(read_only=True)
    patient_name = serializers.CharField(read_only=True)
    token_used = serializers.BooleanField(read_only=True)
    is_linked = serializers.BooleanField(read_only=True)


class LinkPatientAccountSerializer(serializers.Serializer):
    """
    Serializer for linking a patient account to an existing patient record.
    Used when a patient creates an account and provides their linking token.
    """
    linking_token = serializers.CharField(
        max_length=64,
        help_text='The unique linking token provided by the healthcare provider'
    )
    
    def validate_linking_token(self, value):
        """Validate the linking token."""
        try:
            patient_record = PatientRecord.objects.get(linking_token=value)
        except PatientRecord.DoesNotExist:
            raise serializers.ValidationError('Invalid linking token.')
        
        if patient_record.token_used:
            raise serializers.ValidationError('This linking token has already been used.')
        
        if patient_record.linked_user is not None:
            raise serializers.ValidationError('This patient record is already linked to an account.')
        
        return value


class ProviderPatientAccessSerializer(serializers.ModelSerializer):
    """
    Serializer for provider patient access records.
    """
    provider_name = serializers.SerializerMethodField()
    patient_name = serializers.CharField(source='patient_record.full_name', read_only=True)
    
    class Meta:
        model = ProviderPatientAccess
        fields = [
            'id',
            'provider',
            'provider_name',
            'patient_record',
            'patient_name',
            'access_level',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_provider_name(self, obj):
        """Return the provider's display name using centralized utility."""
        from common.utils import get_provider_display_name
        return get_provider_display_name(obj.provider)


class GrantAccessSerializer(serializers.Serializer):
    """
    Serializer for granting access to a patient record.
    """
    patient_record_id = serializers.IntegerField(
        help_text='The ID of the patient record to grant access to'
    )
    provider_id = serializers.IntegerField(
        help_text='The ID of the provider to grant access to'
    )
    access_level = serializers.ChoiceField(
        choices=['FULL', 'READ_ONLY', 'LIMITED'],
        default='FULL',
        help_text='Level of access to grant'
    )
    
    def validate_patient_record_id(self, value):
        """Validate that the patient record exists."""
        try:
            PatientRecord.objects.get(pk=value)
        except PatientRecord.DoesNotExist:
            raise serializers.ValidationError('Patient record not found.')
        return value
    
    def validate_provider_id(self, value):
        """Validate that the provider exists."""
        try:
            Provider.objects.get(pk=value)
        except Provider.DoesNotExist:
            raise serializers.ValidationError('Provider not found.')
        return value


# =============================================================================
# SHARE TOKEN SERIALIZERS
# =============================================================================

class CreateShareTokenSerializer(serializers.Serializer):
    """
    Serializer for creating a new share token.
    Patients can use this to generate time-limited access tokens.
    """
    access_level = serializers.ChoiceField(
        choices=['READ_ONLY', 'FULL', 'LIMITED'],
        default='READ_ONLY',
        help_text='Level of access to grant'
    )
    expires_in_hours = serializers.IntegerField(
        min_value=1,
        max_value=720,  # Max 30 days
        default=24,
        help_text='Hours until token expires (1-720, default 24)'
    )
    max_uses = serializers.IntegerField(
        min_value=0,
        max_value=100,
        default=1,
        help_text='Maximum times token can be used (0 = unlimited)'
    )
    target_provider_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='Optional: Specific provider this token is for'
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text='Optional notes about this share'
    )
    
    def validate_target_provider_id(self, value):
        """Validate that the target provider exists."""
        if value:
            try:
                Provider.objects.get(pk=value)
            except Provider.DoesNotExist:
                raise serializers.ValidationError('Target provider not found.')
        return value


class ShareTokenSerializer(serializers.ModelSerializer):
    """
    Serializer for share tokens (read operations).
    """
    patient_name = serializers.CharField(source='patient_record.full_name', read_only=True)
    patient_unique_id = serializers.CharField(source='patient_record.patient_unique_id', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_usable = serializers.BooleanField(read_only=True)
    target_provider_name = serializers.SerializerMethodField()
    qr_code_data = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalRecordShareToken
        fields = [
            'id',
            'token',
            'patient_name',
            'patient_unique_id',
            'access_level',
            'expires_at',
            'max_uses',
            'use_count',
            'is_active',
            'is_revoked',
            'is_expired',
            'is_usable',
            'target_provider_name',
            'notes',
            'qr_code_data',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_target_provider_name(self, obj):
        """Return the target provider's name if set."""
        if obj.target_provider:
            try:
                provider = obj.target_provider
                if hasattr(provider, 'doctor_profile'):
                    doctor = provider.doctor_profile
                    return f'Dr. {doctor.first_name} {doctor.last_name}'
                elif hasattr(provider, 'nurse_profile'):
                    nurse = provider.nurse_profile
                    return f'{nurse.first_name} {nurse.last_name}'
                elif hasattr(provider, 'clinic_profile'):
                    return provider.clinic_profile.clinic_name
                else:
                    return provider.user.email
            except Exception:
                return str(obj.target_provider)
        return None
    
    def get_qr_code_data(self, obj):
        """Return data for generating QR code on frontend."""
        request = self.context.get('request')
        if request:
            base_url = request.build_absolute_uri('/').rstrip('/')
            share_url = f"{base_url}/api/patients/records/share/{obj.token}/"
        else:
            share_url = f"/api/patients/records/share/{obj.token}/"
        
        return {
            'token': obj.token,
            'url': share_url,
            'patient_id': obj.patient_record.patient_unique_id,
            'expires_at': obj.expires_at.isoformat() if obj.expires_at else None,
        }


class ShareTokenListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing share tokens.
    """
    is_expired = serializers.BooleanField(read_only=True)
    is_usable = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MedicalRecordShareToken
        fields = [
            'id',
            'token',
            'access_level',
            'expires_at',
            'max_uses',
            'use_count',
            'is_active',
            'is_revoked',
            'is_expired',
            'is_usable',
            'created_at',
        ]
        read_only_fields = fields


class ShareTokenAccessLogSerializer(serializers.ModelSerializer):
    """
    Serializer for share token access logs.
    """
    accessed_by_provider_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ShareTokenAccessLog
        fields = [
            'id',
            'share_token',
            'accessed_by_provider_name',
            'accessed_at',
            'ip_address',
        ]
        read_only_fields = fields
    
    def get_accessed_by_provider_name(self, obj):
        """Return the provider's name."""
        if obj.accessed_by_provider:
            try:
                provider = obj.accessed_by_provider
                if hasattr(provider, 'doctor_profile'):
                    doctor = provider.doctor_profile
                    return f'Dr. {doctor.first_name} {doctor.last_name}'
                elif hasattr(provider, 'nurse_profile'):
                    nurse = provider.nurse_profile
                    return f'{nurse.first_name} {nurse.last_name}'
                elif hasattr(provider, 'clinic_profile'):
                    return provider.clinic_profile.clinic_name
                else:
                    return provider.user.email
            except Exception:
                return str(obj.accessed_by_provider)
        return 'Unknown Provider'


class UseShareTokenSerializer(serializers.Serializer):
    """
    Serializer for using a share token to access patient records.
    Used by providers to access records via share token.
    """
    token = serializers.CharField(
        max_length=64,
        help_text='The share token'
    )
    
    def validate_token(self, value):
        """Validate the share token."""
        try:
            share_token = MedicalRecordShareToken.objects.get(token=value)
        except MedicalRecordShareToken.DoesNotExist:
            raise serializers.ValidationError('Invalid share token.')
        
        if not share_token.is_usable:
            if share_token.is_revoked:
                raise serializers.ValidationError('This share token has been revoked.')
            if share_token.is_expired:
                raise serializers.ValidationError('This share token has expired.')
            if share_token.max_uses > 0 and share_token.use_count >= share_token.max_uses:
                raise serializers.ValidationError('This share token has reached maximum uses.')
            raise serializers.ValidationError('This share token is no longer valid.')
        
        return value


class PatientMedicalHistorySerializer(serializers.Serializer):
    """
    Serializer for patient's complete medical history.
    Returns a consolidated view of all medical records.
    """
    patient_info = serializers.SerializerMethodField()
    medical_records_summary = serializers.SerializerMethodField()
    total_records = serializers.IntegerField()
    
    def get_patient_info(self, obj):
        """Return basic patient information."""
        patient_record = obj.get('patient_record')
        if patient_record:
            return {
                'patient_unique_id': patient_record.patient_unique_id,
                'full_name': patient_record.full_name,
                'date_of_birth': patient_record.date_of_birth,
                'age': patient_record.age,
                'gender': patient_record.gender,
                'blood_type': patient_record.blood_type,
                'known_allergies': patient_record.known_allergies,
                'chronic_conditions': patient_record.chronic_conditions,
            }
        return None
    
    def get_medical_records_summary(self, obj):
        """Return summary of medical records by type."""
        records = obj.get('records', [])
        summary = {}
        for record in records:
            record_type = record.record_type
            if record_type not in summary:
                summary[record_type] = {
                    'count': 0,
                    'latest_date': None,
                    'records': []
                }
            summary[record_type]['count'] += 1
            if not summary[record_type]['latest_date'] or record.record_date > summary[record_type]['latest_date']:
                summary[record_type]['latest_date'] = record.record_date
            summary[record_type]['records'].append({
                'id': record.id,
                'title': record.title,
                'record_date': record.record_date,
                'is_confidential': record.is_confidential,
            })
        return summary
