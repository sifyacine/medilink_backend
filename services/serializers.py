"""
Services serializers.
"""
from rest_framework import serializers
from services.models import Service, DoctorService, NurseService
from specialties.models import Specialty
from specialties.serializers import SpecialtySerializer


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model."""
    specialty = SpecialtySerializer(read_only=True)
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        source='specialty',
        write_only=True,
        required=False,
        allow_null=True
    )
    currency_display = serializers.CharField(
        source='get_currency_display',
        read_only=True
    )
    
    class Meta:
        model = Service
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'price',
            'currency',
            'currency_display',
            'duration_minutes',
            'icon',
            'is_home_service',
            'is_active',
            'specialty',
            'specialty_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for specialty_id
        from specialties.models import Specialty
        self.fields['specialty_id'].queryset = Specialty.objects.filter(is_active=True)


class DoctorServiceSerializer(serializers.ModelSerializer):
    """Serializer for DoctorService relationship."""
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True),
        source='service',
        write_only=True
    )
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    final_price = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorService
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'service',
            'service_id',
            'custom_price',
            'final_price',
            'is_available',
            'created_at',
        ]
        read_only_fields = ['id', 'doctor', 'created_at']
    
    def get_final_price(self, obj):
        """Return custom_price if set, otherwise service price."""
        return obj.custom_price if obj.custom_price else obj.service.price


class NurseServiceSerializer(serializers.ModelSerializer):
    """Serializer for NurseService relationship."""
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True),
        source='service',
        write_only=True
    )
    nurse_name = serializers.CharField(source='nurse.full_name', read_only=True)
    final_price = serializers.SerializerMethodField()
    
    class Meta:
        model = NurseService
        fields = [
            'id',
            'nurse',
            'nurse_name',
            'service',
            'service_id',
            'custom_price',
            'final_price',
            'is_available',
            'created_at',
        ]
        read_only_fields = ['id', 'nurse', 'created_at']
    
    def get_final_price(self, obj):
        """Return custom_price if set, otherwise service price."""
        return obj.custom_price if obj.custom_price else obj.service.price
