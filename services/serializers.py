"""
Services serializers with multilingual support.
"""
from rest_framework import serializers
from services.models import Service, DoctorService, NurseService, ProviderCustomService
from specialties.models import Specialty
from specialties.serializers import SpecialtySerializer
from common.i18n import (
    LocalizedFieldsMixin,
    get_language_from_request,
    get_localized_field,
    SUPPORTED_LANGUAGES,
)


class ServiceSerializer(LocalizedFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for Service model with multilingual support.
    
    Automatically localizes title and description based on request language.
    Query params:
    - ?lang=ar|fr|en - Force specific language
    - ?include_all_translations=true - Include all language versions
    """
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
    service_type_display = serializers.CharField(
        source='get_service_type_display',
        read_only=True
    )
    
    # Multilingual fields - these will be replaced with localized versions
    title_translations = serializers.SerializerMethodField()
    description_translations = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        localize_fields = ['title', 'description']  # Fields to auto-localize
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'service_type',
            'service_type_display',
            'price',
            'currency',
            'currency_display',
            'duration_minutes',
            'icon',
            'is_home_service',
            'is_on_demand',
            'is_active',
            'specialty',
            'specialty_id',
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
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for specialty_id
        self.fields['specialty_id'].queryset = Specialty.objects.filter(is_active=True)
        
        # Optionally exclude translation fields from response
        request = self.context.get('request')
        if request and not request.query_params.get('include_all_translations', '').lower() == 'true':
            # Hide individual translation fields and translation dicts
            fields_to_hide = [
                'title_en', 'title_ar', 'title_fr',
                'description_en', 'description_ar', 'description_fr',
                'title_translations', 'description_translations'
            ]
            for field in fields_to_hide:
                if field in self.fields:
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


class ServiceListSerializer(LocalizedFieldsMixin, serializers.ModelSerializer):
    """
    Lightweight serializer for service listings.
    Only includes essential fields with localized content.
    """
    service_type_display = serializers.CharField(
        source='get_service_type_display',
        read_only=True
    )
    specialty_name = serializers.CharField(
        source='specialty.title',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Service
        localize_fields = ['title', 'description']
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'service_type',
            'service_type_display',
            'price',
            'currency',
            'duration_minutes',
            'icon',
            'is_home_service',
            'is_on_demand',
            'specialty_name',
        ]


class ServiceAdminSerializer(serializers.ModelSerializer):
    """
    Admin serializer for Service - includes all multilingual fields for editing.
    """
    specialty = SpecialtySerializer(read_only=True)
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        source='specialty',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Service
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
            # Service details
            'service_type',
            'price',
            'currency',
            'duration_minutes',
            'icon',
            'is_home_service',
            'is_on_demand',
            'is_active',
            'specialty',
            'specialty_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class DoctorServiceSerializer(serializers.ModelSerializer):
    """Serializer for DoctorService relationship with localized service info."""
    service = ServiceListSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True),
        source='service',
        write_only=True
    )
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    effective_duration = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DoctorService
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'service',
            'service_id',
            'custom_price',
            'custom_duration_minutes',
            'effective_price',
            'effective_duration',
            'is_available',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'doctor', 'created_at']


class NurseServiceSerializer(serializers.ModelSerializer):
    """Serializer for NurseService relationship with localized service info."""
    service = ServiceListSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True),
        source='service',
        write_only=True
    )
    nurse_name = serializers.CharField(source='nurse.full_name', read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    effective_duration = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = NurseService
        fields = [
            'id',
            'nurse',
            'nurse_name',
            'service',
            'service_id',
            'custom_price',
            'custom_duration_minutes',
            'effective_price',
            'effective_duration',
            'is_available',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'nurse', 'created_at']


class ProviderCustomServiceSerializer(LocalizedFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for provider custom services with multilingual support.
    """
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
    provider_name = serializers.CharField(
        source='provider.get_display_name',
        read_only=True
    )
    
    class Meta:
        model = ProviderCustomService
        localize_fields = ['title', 'description']
        fields = [
            'id',
            'provider',
            'provider_name',
            'title',
            'description',
            # Multilingual fields for editing
            'title_en',
            'title_ar',
            'title_fr',
            'description_en',
            'description_ar',
            'description_fr',
            # Service details
            'price',
            'currency',
            'currency_display',
            'duration_minutes',
            'specialty',
            'specialty_id',
            'is_active',
            'is_home_service',
            'is_online_available',
            'image',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'provider', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        # Hide multilingual edit fields unless admin or provider
        if request and not (
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'PROVIDER']
        ):
            for field in ['title_en', 'title_ar', 'title_fr', 
                         'description_en', 'description_ar', 'description_fr']:
                self.fields.pop(field, None)
