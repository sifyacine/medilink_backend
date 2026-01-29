"""
Prescription serializers for the Medilink platform.

Handles serialization/deserialization for prescription management:
- Prescription CRUD
- Prescription items (medications)
- PDF file uploads
"""
from rest_framework import serializers
from django.db import transaction

from .models import (
    Prescription, PrescriptionItem, PrescriptionStatus,
    MedicationType, DosageFrequency
)
from appointments.models import Appointment, AppointmentStatus


class PrescriptionItemSerializer(serializers.ModelSerializer):
    """Serializer for individual prescription items (medications)."""
    
    medication_type_display = serializers.CharField(
        source='get_medication_type_display',
        read_only=True
    )
    frequency_display = serializers.CharField(
        source='get_frequency_display',
        read_only=True
    )
    full_instructions = serializers.CharField(
        source='get_full_instructions',
        read_only=True
    )
    
    class Meta:
        model = PrescriptionItem
        fields = [
            'id',
            'medication_name',
            'medication_type',
            'medication_type_display',
            'generic_name',
            'strength',
            'dosage',
            'frequency',
            'frequency_display',
            'custom_frequency',
            'duration_days',
            'duration_text',
            'quantity',
            'quantity_unit',
            'instructions',
            'full_instructions',
            'order',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class PrescriptionItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating prescription items."""
    
    class Meta:
        model = PrescriptionItem
        fields = [
            'medication_name',
            'medication_type',
            'generic_name',
            'strength',
            'dosage',
            'frequency',
            'custom_frequency',
            'duration_days',
            'duration_text',
            'quantity',
            'quantity_unit',
            'instructions',
            'order',
        ]
    
    def validate(self, attrs):
        """Validate custom frequency is provided when frequency is CUSTOM."""
        if attrs.get('frequency') == DosageFrequency.CUSTOM:
            if not attrs.get('custom_frequency'):
                raise serializers.ValidationError({
                    'custom_frequency': 'Custom frequency text is required when frequency is CUSTOM.'
                })
        return attrs


class PrescriptionListSerializer(serializers.ModelSerializer):
    """Serializer for listing prescriptions (compact view)."""
    
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    clinic_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id',
            'reference_number',
            'patient_name',
            'doctor_name',
            'clinic_name',
            'diagnosis',
            'status',
            'status_display',
            'items_count',
            'valid_until',
            'issued_at',
            'created_at',
        ]
    
    def get_patient_name(self, obj):
        return obj.get_patient_display_name()
    
    def get_doctor_name(self, obj):
        return obj.doctor.full_name if obj.doctor else None
    
    def get_clinic_name(self, obj):
        return obj.clinic.name if obj.clinic else None
    
    def get_items_count(self, obj):
        return obj.items.count()


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed prescription view."""
    
    patient_name = serializers.SerializerMethodField()
    patient_id = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    doctor_id = serializers.UUIDField(source='doctor.id', read_only=True)
    clinic_name = serializers.SerializerMethodField()
    clinic_id = serializers.UUIDField(source='clinic.id', read_only=True, allow_null=True)
    appointment_id = serializers.UUIDField(source='appointment.id', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id',
            'reference_number',
            'patient_id',
            'patient_name',
            'doctor_id',
            'doctor_name',
            'clinic_id',
            'clinic_name',
            'appointment_id',
            'diagnosis',
            'notes',
            'instructions',
            'items',
            'status',
            'status_display',
            'is_valid',
            'valid_until',
            'pdf_file',
            'pdf_url',
            'issued_at',
            'created_at',
            'updated_at',
        ]
    
    def get_patient_name(self, obj):
        return obj.get_patient_display_name()
    
    def get_patient_id(self, obj):
        if obj.patient:
            return str(obj.patient.id)
        if obj.patient_record:
            return str(obj.patient_record.id)
        return None
    
    def get_doctor_name(self, obj):
        return obj.doctor.full_name if obj.doctor else None
    
    def get_clinic_name(self, obj):
        return obj.clinic.name if obj.clinic else None
    
    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return None


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating prescriptions.
    
    The doctor is auto-set from the authenticated user.
    Patient can be specified by patient_id (User) or patient_record_id.
    Appointment must be confirmed or completed.
    """
    
    patient_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    patient_record_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    appointment_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    clinic_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    items = PrescriptionItemCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Prescription
        fields = [
            'patient_id',
            'patient_record_id',
            'clinic_id',
            'appointment_id',
            'diagnosis',
            'notes',
            'instructions',
            'valid_until',
            'items',
        ]
    
    def validate(self, attrs):
        """Validate patient and appointment."""
        patient_id = attrs.pop('patient_id', None)
        patient_record_id = attrs.pop('patient_record_id', None)
        appointment_id = attrs.pop('appointment_id', None)
        clinic_id = attrs.pop('clinic_id', None)
        
        # Validate patient
        if not patient_id and not patient_record_id:
            raise serializers.ValidationError({
                'patient_id': 'Either patient_id or patient_record_id must be provided.'
            })
        
        if patient_id and patient_record_id:
            raise serializers.ValidationError({
                'patient_id': 'Cannot specify both patient_id and patient_record_id.'
            })
        
        # Resolve patient
        if patient_id:
            from accounts.models import User
            try:
                attrs['patient'] = User.objects.get(id=patient_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'patient_id': 'Patient not found.'
                })
        
        if patient_record_id:
            from patients.models import PatientRecord
            try:
                attrs['patient_record'] = PatientRecord.objects.get(id=patient_record_id)
            except PatientRecord.DoesNotExist:
                raise serializers.ValidationError({
                    'patient_record_id': 'Patient record not found.'
                })
        
        # Resolve appointment
        if appointment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                valid_statuses = [AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED]
                if appointment.status not in valid_statuses:
                    raise serializers.ValidationError({
                        'appointment_id': 'Prescription can only be created for confirmed or completed appointments.'
                    })
                
                # Check if appointment already has a prescription
                if hasattr(appointment, 'prescription') and appointment.prescription:
                    raise serializers.ValidationError({
                        'appointment_id': 'This appointment already has a prescription.'
                    })
                
                attrs['appointment'] = appointment
            except Appointment.DoesNotExist:
                raise serializers.ValidationError({
                    'appointment_id': 'Appointment not found.'
                })
        
        # Resolve clinic
        if clinic_id:
            from providers.models.clinic import Clinic
            try:
                attrs['clinic'] = Clinic.objects.get(id=clinic_id)
            except Clinic.DoesNotExist:
                raise serializers.ValidationError({
                    'clinic_id': 'Clinic not found.'
                })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Create prescription with items."""
        items_data = validated_data.pop('items', [])
        
        # Get doctor from context
        request = self.context.get('request')
        if request and hasattr(request.user, 'doctor_profile'):
            validated_data['doctor'] = request.user.doctor_profile
        else:
            raise serializers.ValidationError('Only doctors can create prescriptions.')
        
        prescription = Prescription.objects.create(**validated_data)
        
        # Create items
        for idx, item_data in enumerate(items_data):
            item_data['order'] = item_data.get('order', idx)
            PrescriptionItem.objects.create(prescription=prescription, **item_data)
        
        return prescription


class PrescriptionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating prescriptions (only draft status)."""
    
    items = PrescriptionItemCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Prescription
        fields = [
            'diagnosis',
            'notes',
            'instructions',
            'valid_until',
            'items',
        ]
    
    def validate(self, attrs):
        """Only allow updates on draft prescriptions."""
        if self.instance and self.instance.status != PrescriptionStatus.DRAFT:
            raise serializers.ValidationError(
                'Can only update prescriptions in DRAFT status.'
            )
        return attrs
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Update prescription and items."""
        items_data = validated_data.pop('items', None)
        
        # Update prescription fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Replace items if provided
        if items_data is not None:
            instance.items.all().delete()
            for idx, item_data in enumerate(items_data):
                item_data['order'] = item_data.get('order', idx)
                PrescriptionItem.objects.create(prescription=instance, **item_data)
        
        return instance


class PrescriptionPDFUploadSerializer(serializers.Serializer):
    """Serializer for uploading prescription PDF."""
    
    pdf_file = serializers.FileField(required=True)
    
    def validate_pdf_file(self, value):
        """Validate file is PDF and size."""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError('Only PDF files are allowed.')
        
        # Max 10MB
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('File size must not exceed 10MB.')
        
        return value


class PrescriptionIssueSerializer(serializers.Serializer):
    """Serializer for issuing a prescription (draft -> issued)."""
    
    pass  # No additional data required


class PrescriptionStatusSerializer(serializers.Serializer):
    """Serializer for prescription status choices."""
    
    value = serializers.CharField()
    label = serializers.CharField()


class MedicationTypeSerializer(serializers.Serializer):
    """Serializer for medication type choices."""
    
    value = serializers.CharField()
    label = serializers.CharField()


class DosageFrequencySerializer(serializers.Serializer):
    """Serializer for dosage frequency choices."""
    
    value = serializers.CharField()
    label = serializers.CharField()
