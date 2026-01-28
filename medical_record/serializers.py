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


class MedicalRecordAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for medical record attachments."""
    
    uploaded_by_email = serializers.EmailField(source='uploaded_by.email', read_only=True)
    
    class Meta:
        model = MedicalRecordAttachment
        fields = [
            'id',
            'file',
            'file_name',
            'file_type',
            'file_size',
            'description',
            'uploaded_by_email',
            'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by_email']


class MedicalRecordNoteSerializer(serializers.ModelSerializer):
    """Serializer for medical record notes."""
    
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = MedicalRecordNote
        fields = [
            'id',
            'note_type',
            'content',
            'created_by_email',
            'created_at',
            'updated_at',
            'is_locked',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_email', 'is_locked']
    
    def validate(self, attrs):
        """Ensure patients cannot create provider notes."""
        request = self.context.get('request')
        if request and request.user:
            if request.user.role == UserRole.PATIENT:
                if attrs.get('note_type') == 'PROVIDER':
                    raise serializers.ValidationError(
                        'Patients cannot create provider notes.'
                    )
        return attrs


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for prescription information."""
    
    class Meta:
        model = Prescription
        fields = [
            'id',
            'medication_name',
            'dosage',
            'frequency',
            'duration',
            'instructions',
            'quantity',
            'refills',
        ]
        read_only_fields = ['id']


class AllergySerializer(serializers.ModelSerializer):
    """Serializer for allergy information."""
    
    class Meta:
        model = Allergy
        fields = [
            'id',
            'allergen',
            'severity',
            'reaction',
            'first_observed',
        ]
        read_only_fields = ['id']


class MedicalRecordListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing medical records.
    Used in list views for performance.
    """
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    has_prescription = serializers.SerializerMethodField()
    has_allergy = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    note_count = serializers.SerializerMethodField()
    
    def get_has_prescription(self, obj):
        """Check if record has prescription."""
        return hasattr(obj, 'prescription')
    
    def get_has_allergy(self, obj):
        """Check if record has allergy."""
        return hasattr(obj, 'allergy')
    
    def get_attachment_count(self, obj):
        """Get count of attachments."""
        return obj.attachments.count()
    
    def get_note_count(self, obj):
        """Get count of notes."""
        return obj.notes.count()
    
    class Meta:
        model = MedicalRecord
        fields = [
            'id',
            'title',
            'record_type',
            'record_date',
            'patient_email',
            'created_by_email',
            'is_active',
            'requires_followup',
            'followup_date',
            'created_at',
            'has_prescription',
            'has_allergy',
            'attachment_count',
            'note_count',
        ]
        read_only_fields = ['id', 'created_at']


class MedicalRecordDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for medical record details.
    Includes nested prescriptions, allergies, attachments, and notes.
    """
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    updated_by_email = serializers.EmailField(source='updated_by.email', read_only=True)
    
    # Nested serializers
    prescription = PrescriptionSerializer(read_only=True)
    allergy = AllergySerializer(read_only=True)
    attachments = MedicalRecordAttachmentSerializer(many=True, read_only=True)
    notes = MedicalRecordNoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = [
            'id',
            'patient',
            'patient_email',
            'title',
            'record_type',
            'diagnosis_code',
            'description',
            'symptoms',
            'record_date',
            'created_by',
            'created_by_email',
            'updated_by',
            'updated_by_email',
            'is_active',
            'is_confidential',
            'requires_followup',
            'followup_date',
            'created_at',
            'updated_at',
            'prescription',
            'allergy',
            'attachments',
            'notes',
        ]
        read_only_fields = [
            'id',
            'patient',
            'created_by',
            'updated_by',
            'created_at',
            'updated_at',
        ]


class MedicalRecordCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating medical records.
    Patients can create their own records, providers can create for patients.
    """
    prescription = PrescriptionSerializer(required=False, allow_null=True)
    allergy = AllergySerializer(required=False, allow_null=True)
    
    class Meta:
        model = MedicalRecord
        fields = [
            'patient',
            'title',
            'record_type',
            'diagnosis_code',
            'description',
            'symptoms',
            'record_date',
            'is_confidential',
            'requires_followup',
            'followup_date',
            'prescription',
            'allergy',
        ]
    
    def validate_patient(self, value):
        """Ensure patient is valid and user has permission to create records for them."""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError('Authentication required.')
        
        # Patients can only create records for themselves
        if request.user.role == UserRole.PATIENT:
            if value != request.user:
                raise serializers.ValidationError(
                    'Patients can only create medical records for themselves.'
                )
        
        # Providers can create records for any patient
        elif request.user.role == UserRole.PROVIDER:
            if value.role != UserRole.PATIENT:
                raise serializers.ValidationError(
                    'Medical records can only be created for patients.'
                )
        
        # Admins can create records for any patient
        elif request.user.role != UserRole.ADMIN:
            raise serializers.ValidationError('Insufficient permissions.')
        
        return value
    
    def create(self, validated_data):
        """Create medical record with nested prescription/allergy if provided."""
        prescription_data = validated_data.pop('prescription', None)
        allergy_data = validated_data.pop('allergy', None)
        
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        
        medical_record = MedicalRecord.objects.create(**validated_data)
        
        # Create prescription if provided
        if prescription_data:
            Prescription.objects.create(
                medical_record=medical_record,
                **prescription_data
            )
        
        # Create allergy if provided
        if allergy_data:
            Allergy.objects.create(
                medical_record=medical_record,
                **allergy_data
            )
        
        # Log access
        from medical_record.models import MedicalRecordAccessLog
        MedicalRecordAccessLog.objects.create(
            medical_record=medical_record,
            accessed_by=request.user,
            access_type='CREATE',
            ip_address=self._get_client_ip(request)
        )
        
        return medical_record
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class MedicalRecordUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating medical records.
    Enforces permission rules: patients cannot modify provider-locked fields.
    """
    prescription = PrescriptionSerializer(required=False, allow_null=True)
    allergy = AllergySerializer(required=False, allow_null=True)
    
    class Meta:
        model = MedicalRecord
        fields = [
            'title',
            'record_type',
            'diagnosis_code',
            'description',
            'symptoms',
            'record_date',
            'is_active',
            'is_confidential',
            'requires_followup',
            'followup_date',
            'prescription',
            'allergy',
        ]
    
    def validate(self, attrs):
        """Ensure patients cannot modify provider-created records inappropriately."""
        request = self.context.get('request')
        instance = self.instance
        
        if request and request.user:
            # If record was created by a provider, patients have limited edit rights
            if (
                request.user.role == UserRole.PATIENT and
                instance.created_by and
                instance.created_by.role == UserRole.PROVIDER
            ):
                # Patients can only update certain fields on provider-created records
                restricted_fields = ['diagnosis_code', 'record_type']
                for field in restricted_fields:
                    if field in attrs:
                        raise serializers.ValidationError(
                            f'Patients cannot modify {field} on provider-created records.'
                        )
        
        return attrs
    
    def update(self, instance, validated_data):
        """Update medical record and nested objects."""
        prescription_data = validated_data.pop('prescription', None)
        allergy_data = validated_data.pop('allergy', None)
        
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        
        # Update main record
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or create prescription
        if prescription_data is not None:
            if hasattr(instance, 'prescription'):
                for attr, value in prescription_data.items():
                    setattr(instance.prescription, attr, value)
                instance.prescription.save()
            else:
                Prescription.objects.create(
                    medical_record=instance,
                    **prescription_data
                )
        
        # Update or create allergy
        if allergy_data is not None:
            if hasattr(instance, 'allergy'):
                for attr, value in allergy_data.items():
                    setattr(instance.allergy, attr, value)
                instance.allergy.save()
            else:
                Allergy.objects.create(
                    medical_record=instance,
                    **allergy_data
                )
        
        # Log access
        from medical_record.models import MedicalRecordAccessLog
        MedicalRecordAccessLog.objects.create(
            medical_record=instance,
            accessed_by=request.user,
            access_type='UPDATE',
            ip_address=self._get_client_ip(request)
        )
        
        return instance
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class ProviderAccessSerializer(serializers.ModelSerializer):
    """Serializer for viewing provider access grants."""
    
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    patient_name = serializers.SerializerMethodField()
    provider_email = serializers.EmailField(source='provider.user.email', read_only=True)
    provider_name = serializers.SerializerMethodField()
    access_type_display = serializers.CharField(source='get_access_type_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = ProviderAccess
        fields = [
            'id',
            'patient',
            'patient_email',
            'patient_name',
            'provider',
            'provider_email',
            'provider_name',
            'access_type',
            'access_type_display',
            'granted_at',
            'expires_at',
            'is_active',
            'is_expired',
            'is_valid',
            'reason',
        ]
        read_only_fields = [
            'id',
            'granted_at',
            'patient_email',
            'patient_name',
            'provider_email',
            'provider_name',
        ]
    
    def get_patient_name(self, obj):
        if obj.patient.first_name:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return obj.patient.email
    
    def get_provider_name(self, obj):
        if obj.provider.user.first_name:
            return f"{obj.provider.user.first_name} {obj.provider.user.last_name}"
        return obj.provider.user.email
    
    def get_is_valid(self, obj):
        return obj.is_valid()


class ProviderAccessCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating provider access grants."""
    
    provider_id = serializers.UUIDField(write_only=True)
    patient_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = ProviderAccess
        fields = [
            'provider_id',
            'patient_id',
            'access_type',
            'expires_at',
            'reason',
        ]
    
    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        
        # Get provider
        provider_id = attrs.pop('provider_id')
        try:
            from providers.models import Provider
            provider = Provider.objects.get(id=provider_id)
            attrs['provider'] = provider
        except Exception:
            raise serializers.ValidationError({'provider_id': 'Provider not found.'})
        
        # Get patient
        if user.role == UserRole.PATIENT:
            # Patients can only grant access to their own records
            attrs['patient'] = user
        else:
            # Admins need to specify patient
            patient_id = attrs.pop('patient_id', None)
            if not patient_id:
                raise serializers.ValidationError({'patient_id': 'Patient ID is required for admins.'})
            try:
                patient = User.objects.get(id=patient_id, role=UserRole.PATIENT)
                attrs['patient'] = patient
            except User.DoesNotExist:
                raise serializers.ValidationError({'patient_id': 'Patient not found.'})
        
        # Check for existing access
        existing = ProviderAccess.objects.filter(
            patient=attrs['patient'],
            provider=attrs['provider']
        ).first()
        
        if existing:
            raise serializers.ValidationError(
                'Access grant already exists for this provider and patient. '
                'Use the update endpoint to modify it.'
            )
        
        # Validate expiration
        if attrs.get('expires_at') and attrs['expires_at'] <= timezone.now():
            raise serializers.ValidationError({'expires_at': 'Expiration date must be in the future.'})
        
        return attrs
