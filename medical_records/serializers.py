"""
Medical Records serializers.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from medical_records.models import (
    MedicalRecord,
    Prescription,
    Allergy,
    MedicalRecordAttachment,
    MedicalRecordNote,
    ProviderAccess,
)
from accounts.serializers.user import UserPublicSerializer
from providers.serializers.provider import ProviderPublicSerializer

User = get_user_model()


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for Prescription model."""
    
    class Meta:
        model = Prescription
        fields = [
            'id',
            'medication_name',
            'dosage',
            'frequency',
            'duration',
            'instructions',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AllergySerializer(serializers.ModelSerializer):
    """Serializer for Allergy model."""
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    
    class Meta:
        model = Allergy
        fields = [
            'id',
            'allergen',
            'severity',
            'severity_display',
            'reaction',
            'diagnosed_date',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MedicalRecordAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRecordAttachment model."""
    file_type_display = serializers.CharField(
        source='get_file_type_display',
        read_only=True
    )
    uploaded_by_email = serializers.EmailField(
        source='uploaded_by.email',
        read_only=True
    )
    
    class Meta:
        model = MedicalRecordAttachment
        fields = [
            'id',
            'file',
            'file_type',
            'file_type_display',
            'description',
            'uploaded_by_email',
            'created_at',
        ]
        read_only_fields = ['id', 'uploaded_by_email', 'created_at']


class MedicalRecordNoteSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRecordNote model."""
    note_type_display = serializers.CharField(
        source='get_note_type_display',
        read_only=True
    )
    author_email = serializers.EmailField(
        source='author.email',
        read_only=True
    )
    
    class Meta:
        model = MedicalRecordNote
        fields = [
            'id',
            'note_type',
            'note_type_display',
            'content',
            'is_visible_to_patient',
            'author_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'author_email', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate note creation based on user role."""
        request = self.context.get('request')
        if request and request.user:
            # Patients can only create patient notes
            if request.user.role == 'PATIENT':
                if attrs.get('note_type') != 'PATIENT':
                    raise serializers.ValidationError(
                        'Patients can only create patient notes.'
                    )
            # Providers can create provider notes
            elif request.user.role == 'PROVIDER':
                if attrs.get('note_type') not in ['PROVIDER', 'SYSTEM']:
                    raise serializers.ValidationError(
                        'Providers can only create provider or system notes.'
                    )
        return attrs


class MedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRecord model."""
    record_type_display = serializers.CharField(
        source='get_record_type_display',
        read_only=True
    )
    patient_email = serializers.EmailField(
        source='patient.email',
        read_only=True
    )
    provider_info = ProviderPublicSerializer(
        source='provider',
        read_only=True
    )
    prescriptions = PrescriptionSerializer(
        many=True,
        read_only=True
    )
    attachments = MedicalRecordAttachmentSerializer(
        many=True,
        read_only=True
    )
    record_notes = MedicalRecordNoteSerializer(
        many=True,
        read_only=True
    )
    created_by_email = serializers.EmailField(
        source='created_by.email',
        read_only=True,
        allow_null=True
    )
    updated_by_email = serializers.EmailField(
        source='updated_by.email',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = MedicalRecord
        fields = [
            'id',
            'patient',
            'patient_email',
            'provider',
            'provider_info',
            'title',
            'record_type',
            'record_type_display',
            'diagnosis',
            'symptoms',
            'treatment',
            'notes',
            'record_date',
            'is_active',
            'is_confidential',
            'prescriptions',
            'attachments',
            'record_notes',
            'created_at',
            'updated_at',
            'created_by_email',
            'updated_by_email',
        ]
        read_only_fields = [
            'id',
            'patient',
            'created_at',
            'updated_at',
            'created_by_email',
            'updated_by_email',
        ]
    
    def validate(self, attrs):
        """Validate record creation and updates."""
        request = self.context.get('request')
        
        if request and request.user:
            # Patients can only create records for themselves
            if request.user.role == 'PATIENT':
                if 'patient' in attrs and attrs['patient'] != request.user:
                    raise serializers.ValidationError(
                        'Patients can only create records for themselves.'
                    )
                # Set patient to current user if not provided
                if 'patient' not in attrs:
                    attrs['patient'] = request.user
            
            # Set created_by/updated_by
            if self.instance is None:  # Creating new record
                attrs['created_by'] = request.user
            else:  # Updating existing record
                attrs['updated_by'] = request.user
        
        return attrs


class ProviderAccessSerializer(serializers.ModelSerializer):
    """Serializer for ProviderAccess model."""
    access_type_display = serializers.CharField(
        source='get_access_type_display',
        read_only=True
    )
    patient_email = serializers.EmailField(
        source='patient.email',
        read_only=True
    )
    provider_email = serializers.EmailField(
        source='provider.user.email',
        read_only=True
    )
    granted_by_email = serializers.EmailField(
        source='access_granted_by.email',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ProviderAccess
        fields = [
            'id',
            'patient',
            'patient_email',
            'provider',
            'provider_email',
            'access_type',
            'access_type_display',
            'granted_at',
            'expires_at',
            'is_active',
            'notes',
            'granted_by_email',
        ]
        read_only_fields = [
            'id',
            'granted_at',
            'granted_by_email',
        ]
