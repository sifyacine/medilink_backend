"""
Specialties serializers with multilingual support.
"""
from rest_framework import serializers
from specialties.models import Specialty, DoctorSpecialty
from providers.models.doctor import Doctor
from common.i18n import (
    LocalizedFieldsMixin,
    get_language_from_request,
    get_localized_field,
)


class SpecialtySerializer(LocalizedFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for Specialty model with multilingual support.
    
    Automatically localizes title and description based on request language.
    Query params:
    - ?lang=ar|fr|en - Force specific language
    - ?include_all_translations=true - Include all language versions
    """
    title_translations = serializers.SerializerMethodField()
    description_translations = serializers.SerializerMethodField()
    doctors_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Specialty
        localize_fields = ['title', 'description']
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'medical_domain',
            'icon',
            'is_active',
            # Multilingual fields for admin/editing
            'title_en',
            'title_ar',
            'title_fr',
            'description_en',
            'description_ar',
            'description_fr',
            # All translations (optional)
            'title_translations',
            'description_translations',
            # SEO
            'meta_title',
            'meta_description',
            # Stats
            'doctors_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        
        # Optionally exclude translation fields from response
        if request and not request.query_params.get('include_all_translations', '').lower() == 'true':
            fields_to_hide = [
                'title_en', 'title_ar', 'title_fr',
                'description_en', 'description_ar', 'description_fr',
                'title_translations', 'description_translations',
                'meta_title', 'meta_description'
            ]
            for field in fields_to_hide:
                self.fields.pop(field, None)
    
    def get_title_translations(self, obj):
        """Return all title translations."""
        return {
            'en': obj.title_en or obj.title,
            'ar': obj.title_ar or '',
            'fr': obj.title_fr or '',
        }
    
    def get_description_translations(self, obj):
        """Return all description translations."""
        return {
            'en': obj.description_en or obj.description,
            'ar': obj.description_ar or '',
            'fr': obj.description_fr or '',
        }
    
    def get_doctors_count(self, obj):
        """Return count of doctors with this specialty."""
        return obj.specialty_doctors.filter(doctor__provider__is_verified=True).count()


class SpecialtyListSerializer(LocalizedFieldsMixin, serializers.ModelSerializer):
    """
    Lightweight serializer for specialty listings.
    Only includes essential fields with localized content.
    """
    doctors_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Specialty
        localize_fields = ['title', 'description']
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'medical_domain',
            'icon',
            'doctors_count',
        ]
    
    def get_doctors_count(self, obj):
        """Return count of verified doctors with this specialty."""
        return getattr(obj, 'doctors_count', 0)


class SpecialtyAdminSerializer(serializers.ModelSerializer):
    """
    Admin serializer for Specialty - includes all multilingual fields for editing.
    """
    class Meta:
        model = Specialty
        fields = [
            'id',
            'title',
            'slug',
            # All multilingual fields
            'title_en',
            'title_ar',
            'title_fr',
            'description',
            'description_en',
            'description_ar',
            'description_fr',
            # Details
            'medical_domain',
            'icon',
            'is_active',
            # SEO
            'meta_title',
            'meta_description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class DoctorSpecialtySerializer(serializers.ModelSerializer):
    """Serializer for DoctorSpecialty relationship with localized specialty info."""
    specialty = SpecialtyListSerializer(read_only=True)
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
