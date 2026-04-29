"""
Serializers for Medical Records app.
"""
from rest_framework import serializers
from django.utils import timezone
from accounts.models import User
from common.enums import UserRole

from medical_record.models import (
    MedicalRecord,
    Prescription,
    Allergy,
    MedicalRecordAttachment,
    MedicalRecordNote,
    ProviderAccess,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_provider_display_name(provider):
    """Return the human-readable name for a provider using their sub-profile."""
    try:
        from common.enums import ProviderType
        pt = provider.provider_type
        if pt == ProviderType.DOCTOR:
            d = provider.doctor_profile
            return f"Dr. {d.first_name} {d.last_name}".strip()
        if pt == ProviderType.NURSE:
            n = provider.nurse_profile
            return f"{n.first_name} {n.last_name}".strip()
        if pt == ProviderType.CLINIC:
            return provider.clinic_profile.clinic_name
        if pt == ProviderType.LABORATORY:
            return provider.laboratory_profile.lab_name
        if pt == ProviderType.SELLER:
            return provider.seller_profile.business_name
        if pt == ProviderType.VTC:
            return provider.vtc_profile.company_name
    except Exception:
        pass
    return provider.user.email


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# ---------------------------------------------------------------------------
# Sub-record serializers
# ---------------------------------------------------------------------------

class MedicalRecordAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(source='uploaded_by.email', read_only=True)
    file = serializers.SerializerMethodField()

    class Meta:
        model = MedicalRecordAttachment
        fields = [
            'id', 'file', 'file_name', 'file_type', 'file_size',
            'description', 'uploaded_by_email', 'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by_email']

    def get_file(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None


class MedicalRecordNoteSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_role = serializers.CharField(source='created_by.role', read_only=True)

    class Meta:
        model = MedicalRecordNote
        fields = [
            'id', 'note_type', 'content',
            'created_by_email', 'created_by_role',
            'created_at', 'updated_at', 'is_locked',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_email', 'created_by_role', 'is_locked']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user:
            if request.user.role == UserRole.PATIENT and attrs.get('note_type') == 'PROVIDER':
                raise serializers.ValidationError('Patients cannot create provider notes.')
        return attrs


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ['id', 'medication_name', 'dosage', 'frequency', 'duration', 'instructions', 'quantity', 'refills']
        read_only_fields = ['id']


class AllergySerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergy
        fields = ['id', 'allergen', 'severity', 'reaction', 'first_observed']
        read_only_fields = ['id']


# ---------------------------------------------------------------------------
# Medical record list serializer (lightweight)
# ---------------------------------------------------------------------------

class MedicalRecordListSerializer(serializers.ModelSerializer):
    """Compact row for list views — works for both account-linked and offline patients."""
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    patient_name = serializers.SerializerMethodField()
    patient_record_id = serializers.IntegerField(source='patient_record.id', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    has_prescription = serializers.SerializerMethodField()
    has_allergy = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    note_count = serializers.SerializerMethodField()
    severity_display = serializers.CharField(source='get_severity_level_display', read_only=True)
    record_type_display = serializers.SerializerMethodField()

    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'title', 'record_type', 'record_type_display', 'record_date',
            'patient_email', 'patient_name', 'patient_record_id',
            'created_by_email', 'created_by_name',
            'is_active', 'is_confidential',
            'requires_followup', 'followup_date',
            'folder_name', 'severity_level', 'severity_display', 'sequence_number',
            'has_prescription', 'has_allergy', 'attachment_count', 'note_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_patient_name(self, obj):
        if obj.patient:
            name = f"{getattr(obj.patient, 'first_name', '')} {getattr(obj.patient, 'last_name', '')}".strip()
            return name or obj.patient.email
        if obj.patient_record:
            return obj.patient_record.full_name or obj.patient_record.patient_unique_id
        return None

    def get_created_by_name(self, obj):
        if obj.created_by:
            try:
                return _get_provider_display_name(obj.created_by.provider_profile)
            except Exception:
                pass
            return obj.created_by.email
        return None

    def get_has_prescription(self, obj):
        return hasattr(obj, 'prescription') and obj.prescription is not None

    def get_has_allergy(self, obj):
        return hasattr(obj, 'allergy') and obj.allergy is not None

    def get_attachment_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'attachments' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['attachments'])
        return obj.attachments.count()

    def get_note_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'notes' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['notes'])
        return obj.notes.count()

    def get_record_type_display(self, obj):
        return dict(MedicalRecord._meta.get_field('record_type').choices).get(obj.record_type, obj.record_type)


# ---------------------------------------------------------------------------
# Medical record detail serializer
# ---------------------------------------------------------------------------

class MedicalRecordDetailSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    patient_name = serializers.SerializerMethodField()
    patient_record_id = serializers.IntegerField(source='patient_record.id', read_only=True)
    patient_unique_id = serializers.CharField(source='patient_record.patient_unique_id', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    updated_by_email = serializers.EmailField(source='updated_by.email', read_only=True)
    severity_display = serializers.CharField(source='get_severity_level_display', read_only=True)
    record_type_display = serializers.SerializerMethodField()

    prescription = PrescriptionSerializer(read_only=True)
    allergy = AllergySerializer(read_only=True)
    attachments = MedicalRecordAttachmentSerializer(many=True, read_only=True)
    notes = MedicalRecordNoteSerializer(many=True, read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            'id',
            'patient', 'patient_email', 'patient_name',
            'patient_record_id', 'patient_unique_id',
            'title', 'record_type', 'record_type_display',
            'diagnosis_code', 'description', 'symptoms',
            'record_date',
            'created_by', 'created_by_email', 'created_by_name',
            'updated_by', 'updated_by_email',
            'is_active', 'is_confidential',
            'requires_followup', 'followup_date',
            'folder_name', 'severity_level', 'severity_display',
            'sequence_number', 'timeline_order',
            'created_at', 'updated_at',
            'prescription', 'allergy', 'attachments', 'notes',
        ]
        read_only_fields = [
            'id', 'patient', 'created_by', 'updated_by', 'created_at', 'updated_at',
        ]

    def get_patient_name(self, obj):
        if obj.patient:
            name = f"{getattr(obj.patient, 'first_name', '')} {getattr(obj.patient, 'last_name', '')}".strip()
            return name or obj.patient.email
        if obj.patient_record:
            return obj.patient_record.full_name or obj.patient_record.patient_unique_id
        return None

    def get_created_by_name(self, obj):
        if obj.created_by:
            try:
                return _get_provider_display_name(obj.created_by.provider_profile)
            except Exception:
                pass
            return obj.created_by.email
        return None

    def get_record_type_display(self, obj):
        return dict(MedicalRecord._meta.get_field('record_type').choices).get(obj.record_type, obj.record_type)


# ---------------------------------------------------------------------------
# Create serializer
# ---------------------------------------------------------------------------

class MedicalRecordCreateSerializer(serializers.ModelSerializer):
    prescription = PrescriptionSerializer(required=False, allow_null=True)
    allergy = AllergySerializer(required=False, allow_null=True)
    patient_record_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = MedicalRecord
        fields = [
            'patient', 'patient_record_id',
            'title', 'record_type', 'diagnosis_code', 'description', 'symptoms',
            'record_date', 'is_confidential',
            'requires_followup', 'followup_date',
            'prescription', 'allergy',
            'folder_name', 'severity_level', 'sequence_number',
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError('Authentication required.')

        patient = attrs.get('patient')
        patient_record_id = attrs.pop('patient_record_id', None)
        patient_record = None

        if patient_record_id:
            from patients.models import PatientRecord
            try:
                patient_record = PatientRecord.objects.get(id=patient_record_id)
            except PatientRecord.DoesNotExist:
                raise serializers.ValidationError({'patient_record_id': 'Patient record not found.'})

        if not patient and not patient_record:
            raise serializers.ValidationError('Either patient or patient_record_id must be provided.')

        if patient and patient_record and patient_record.linked_user and patient_record.linked_user != patient:
            raise serializers.ValidationError(
                'Provided patient does not match the linked user of patient_record.'
            )

        user = request.user
        if user.role == UserRole.PATIENT:
            if patient and patient != user:
                raise serializers.ValidationError('Patients can only create records for themselves.')
            if patient_record and patient_record.linked_user != user:
                raise serializers.ValidationError(
                    'Patients can only create records linked to their own patient record.'
                )
            attrs['patient'] = user
            if patient_record:
                attrs['patient_record'] = patient_record
        elif user.role in (UserRole.PROVIDER, UserRole.ADMIN):
            if patient and patient.role != UserRole.PATIENT:
                raise serializers.ValidationError('Medical records can only be created for patients.')
            if patient_record:
                attrs['patient_record'] = patient_record
        else:
            raise serializers.ValidationError('Insufficient permissions.')

        # followup_date must be provided and in the future when requires_followup is True
        if attrs.get('requires_followup'):
            followup_date = attrs.get('followup_date')
            if not followup_date:
                raise serializers.ValidationError(
                    {'followup_date': 'followup_date is required when requires_followup is True.'}
                )
            if followup_date < timezone.now().date():
                raise serializers.ValidationError(
                    {'followup_date': 'followup_date must be today or a future date.'}
                )

        return attrs

    def create(self, validated_data):
        prescription_data = validated_data.pop('prescription', None)
        allergy_data = validated_data.pop('allergy', None)

        request = self.context.get('request')
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user

        medical_record = MedicalRecord.objects.create(**validated_data)

        if prescription_data:
            Prescription.objects.create(medical_record=medical_record, **prescription_data)

        if allergy_data:
            Allergy.objects.create(medical_record=medical_record, **allergy_data)

        from medical_record.models import MedicalRecordAccessLog
        MedicalRecordAccessLog.objects.create(
            medical_record=medical_record,
            accessed_by=request.user,
            access_type='CREATE',
            ip_address=_get_client_ip(request),
        )

        return medical_record


# ---------------------------------------------------------------------------
# Update serializer
# ---------------------------------------------------------------------------

class MedicalRecordUpdateSerializer(serializers.ModelSerializer):
    prescription = PrescriptionSerializer(required=False, allow_null=True)
    allergy = AllergySerializer(required=False, allow_null=True)

    class Meta:
        model = MedicalRecord
        fields = [
            'title', 'record_type', 'diagnosis_code', 'description', 'symptoms',
            'record_date', 'is_active', 'is_confidential',
            'requires_followup', 'followup_date',
            'prescription', 'allergy',
            'folder_name', 'severity_level', 'sequence_number', 'timeline_order',
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        instance = self.instance

        if request and request.user:
            if (
                request.user.role == UserRole.PATIENT and
                instance.created_by and
                instance.created_by.role == UserRole.PROVIDER
            ):
                restricted = ['diagnosis_code', 'record_type']
                for field in restricted:
                    if field in attrs:
                        raise serializers.ValidationError(
                            f'Patients cannot modify {field} on provider-created records.'
                        )

        # Validate followup_date
        requires_followup = attrs.get('requires_followup', instance.requires_followup)
        followup_date = attrs.get('followup_date', instance.followup_date)
        if requires_followup:
            if not followup_date:
                raise serializers.ValidationError(
                    {'followup_date': 'followup_date is required when requires_followup is True.'}
                )
            if followup_date < timezone.now().date():
                raise serializers.ValidationError(
                    {'followup_date': 'followup_date must be today or a future date.'}
                )

        return attrs

    def update(self, instance, validated_data):
        prescription_data = validated_data.pop('prescription', None)
        allergy_data = validated_data.pop('allergy', None)

        request = self.context.get('request')
        validated_data['updated_by'] = request.user

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if prescription_data is not None:
            if hasattr(instance, 'prescription') and instance.prescription:
                for attr, value in prescription_data.items():
                    setattr(instance.prescription, attr, value)
                instance.prescription.save()
            else:
                Prescription.objects.create(medical_record=instance, **prescription_data)

        if allergy_data is not None:
            if hasattr(instance, 'allergy') and instance.allergy:
                for attr, value in allergy_data.items():
                    setattr(instance.allergy, attr, value)
                instance.allergy.save()
            else:
                Allergy.objects.create(medical_record=instance, **allergy_data)

        from medical_record.models import MedicalRecordAccessLog
        MedicalRecordAccessLog.objects.create(
            medical_record=instance,
            accessed_by=request.user,
            access_type='UPDATE',
            ip_address=_get_client_ip(request),
        )

        return instance


# ---------------------------------------------------------------------------
# Provider access serializers
# ---------------------------------------------------------------------------

class ProviderAccessSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    patient_name = serializers.SerializerMethodField()
    provider_email = serializers.EmailField(source='provider.user.email', read_only=True)
    provider_name = serializers.SerializerMethodField()
    provider_type = serializers.CharField(source='provider.provider_type', read_only=True)
    access_type_display = serializers.CharField(source='get_access_type_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = ProviderAccess
        fields = [
            'id',
            'patient', 'patient_email', 'patient_name',
            'provider', 'provider_email', 'provider_name', 'provider_type',
            'access_type', 'access_type_display',
            'granted_at', 'expires_at',
            'is_active', 'is_expired', 'is_valid',
            'reason',
        ]
        read_only_fields = [
            'id', 'granted_at',
            'patient_email', 'patient_name',
            'provider_email', 'provider_name', 'provider_type',
        ]

    def get_patient_name(self, obj):
        name = f"{getattr(obj.patient, 'first_name', '')} {getattr(obj.patient, 'last_name', '')}".strip()
        return name or obj.patient.email

    def get_provider_name(self, obj):
        return _get_provider_display_name(obj.provider)

    def get_is_valid(self, obj):
        return obj.is_valid()


class ProviderAccessCreateSerializer(serializers.ModelSerializer):
    """
    Create or reactivate a ProviderAccess grant.

    If a grant already exists for this (patient, provider) pair and is inactive
    (was previously revoked), it is reactivated with the new terms instead of
    raising a conflict error.
    """
    # Provider and User PKs are BigAutoField integers, not UUIDs
    provider_id = serializers.IntegerField(write_only=True)
    patient_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ProviderAccess
        fields = ['provider_id', 'patient_id', 'access_type', 'expires_at', 'reason']

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user

        provider_id = attrs.pop('provider_id')
        try:
            from providers.models import Provider
            provider = Provider.objects.get(id=provider_id)
        except Provider.DoesNotExist:
            raise serializers.ValidationError({'provider_id': 'Provider not found.'})

        # Only APPROVED providers can be granted access
        from common.enums import ProviderStatus
        if provider.status != ProviderStatus.APPROVED:
            raise serializers.ValidationError(
                {'provider_id': 'Access can only be granted to approved providers.'}
            )

        attrs['provider'] = provider

        if user.role == UserRole.PATIENT:
            attrs['patient'] = user
        else:
            patient_id = attrs.pop('patient_id', None)
            if not patient_id:
                raise serializers.ValidationError({'patient_id': 'patient_id is required for admin actions.'})
            try:
                patient = User.objects.get(id=patient_id, role=UserRole.PATIENT)
                attrs['patient'] = patient
            except User.DoesNotExist:
                raise serializers.ValidationError({'patient_id': 'Patient not found.'})

        if attrs.get('expires_at') and attrs['expires_at'] <= timezone.now():
            raise serializers.ValidationError({'expires_at': 'expires_at must be in the future.'})

        return attrs

    def create(self, validated_data):
        """Use update_or_create so a previously revoked grant can be reactivated."""
        patient = validated_data.pop('patient')
        provider = validated_data.pop('provider')
        validated_data.pop('patient_id', None)

        obj, created = ProviderAccess.objects.update_or_create(
            patient=patient,
            provider=provider,
            defaults={
                'access_type': validated_data.get('access_type', 'READ_ONLY'),
                'expires_at': validated_data.get('expires_at'),
                'reason': validated_data.get('reason', ''),
                'is_active': True,
                'access_granted_by': self.context['request'].user,
                'granted_at': timezone.now(),
            },
        )
        return obj


class MedicalRecordAccessLogSerializer(serializers.Serializer):
    """Read-only serializer for access log entries."""
    id = serializers.IntegerField(read_only=True)
    accessed_by_email = serializers.EmailField(source='accessed_by.email', read_only=True)
    accessed_by_role = serializers.CharField(source='accessed_by.role', read_only=True)
    access_type = serializers.CharField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    accessed_at = serializers.DateTimeField(read_only=True)
