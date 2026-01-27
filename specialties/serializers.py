"""
Specialties serializers.
"""
from rest_framework import serializers
from specialties.models import Specialty, DoctorSpecialty
from providers.models.doctor import Doctor


class SpecialtySerializer(serializers.ModelSerializer):
    """Serializer for Specialty model."""
    
    class Meta:
        model = Specialty
        fields = [
            'id',
            'title',
            'title_ar',
            'title_fr',
            'title_en',
            'slug',
            'description',
            'description_ar',
            'description_fr',
            'description_en',
            'medical_domain',
            'icon',
            'is_active',
            'meta_title',
            'meta_description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class DoctorSpecialtySerializer(serializers.ModelSerializer):
    """Serializer for DoctorSpecialty relationship."""
    specialty = SpecialtySerializer(read_only=True)
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.filter(is_active=True),
        source='specialty',
        write_only=True
    )
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    
    class Meta:
        model = DoctorSpecialty
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'specialty',
            'specialty_id',
            'is_primary',
            'years_of_experience',
            'created_at',
        ]
        read_only_fields = ['id', 'doctor', 'created_at']


class DoctorSpecialtyCreateSerializer(serializers.Serializer):
    """Serializer for creating doctor specialty relationships."""
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.filter(is_active=True)
    )
    is_primary = serializers.BooleanField(default=False)
    years_of_experience = serializers.IntegerField(required=False, allow_null=True)
