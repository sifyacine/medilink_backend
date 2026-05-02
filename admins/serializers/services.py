"""
Admin serializers for the Services catalog.
Used exclusively by admin-facing REST API endpoints.
"""
from rest_framework import serializers
from services.models import Service, DoctorService, NurseService, ProviderCustomService


class AdminServiceListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer — includes provider adoption counts."""
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    specialty_name = serializers.CharField(source='specialty.title', read_only=True, allow_null=True)
    nurse_count = serializers.SerializerMethodField()
    doctor_count = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'title', 'slug', 'service_type', 'service_type_display',
            'price', 'currency', 'currency_display',
            'duration_minutes', 'specialty_name',
            'is_active', 'is_home_service', 'is_on_demand',
            'nurse_count', 'doctor_count',
            'created_at', 'updated_at',
        ]

    def get_nurse_count(self, obj):
        return obj.nurses.count()

    def get_doctor_count(self, obj):
        return obj.doctors.count()


class AdminServiceDetailSerializer(serializers.ModelSerializer):
    """
    Full detail serializer — all multilingual fields, all flags.
    Used for create, retrieve, and update.
    """
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    specialty_name = serializers.CharField(source='specialty.title', read_only=True, allow_null=True)
    nurse_count = serializers.SerializerMethodField()
    doctor_count = serializers.SerializerMethodField()
    nurse_assignments = serializers.SerializerMethodField()
    doctor_assignments = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'title', 'slug',
            # Translations
            'title_en', 'title_ar', 'title_fr',
            'description', 'description_en', 'description_ar', 'description_fr',
            # Type & classification
            'service_type', 'service_type_display',
            'specialty', 'specialty_name',
            # Pricing
            'price', 'currency', 'currency_display',
            # Details
            'duration_minutes', 'icon',
            # Flags
            'is_active', 'is_home_service', 'is_on_demand',
            # Provider adoption
            'nurse_count', 'doctor_count',
            'nurse_assignments', 'doctor_assignments',
            # Meta
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_nurse_count(self, obj):
        return obj.nurses.count()

    def get_doctor_count(self, obj):
        return obj.doctors.count()

    def get_nurse_assignments(self, obj):
        """Nurses who have adopted this service, with their pricing."""
        return [
            {
                'id': ns.id,
                'nurse_id': ns.nurse.provider.id,
                'nurse_name': ns.nurse.full_name,
                'custom_price': ns.custom_price,
                'effective_price': ns.effective_price,
                'is_available': ns.is_available,
            }
            for ns in obj.nurses.select_related('nurse__provider').all()
        ]

    def get_doctor_assignments(self, obj):
        """Doctors who have adopted this service, with their pricing."""
        return [
            {
                'id': ds.id,
                'doctor_id': ds.doctor.provider.id,
                'doctor_name': ds.doctor.full_name,
                'custom_price': ds.custom_price,
                'effective_price': ds.effective_price,
                'is_available': ds.is_available,
            }
            for ds in obj.doctors.select_related('doctor__provider').all()
        ]


class AdminNurseServiceSerializer(serializers.ModelSerializer):
    """Admin view of a nurse↔service assignment."""
    nurse_name = serializers.CharField(source='nurse.full_name', read_only=True)
    nurse_provider_id = serializers.IntegerField(source='nurse.provider.id', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    service_type = serializers.CharField(source='service.service_type', read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = NurseService
        fields = [
            'id', 'nurse', 'nurse_name', 'nurse_provider_id',
            'service', 'service_title', 'service_type',
            'custom_price', 'effective_price',
            'is_available', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AdminDoctorServiceSerializer(serializers.ModelSerializer):
    """Admin view of a doctor↔service assignment."""
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    doctor_provider_id = serializers.IntegerField(source='doctor.provider.id', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    service_type = serializers.CharField(source='service.service_type', read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = DoctorService
        fields = [
            'id', 'doctor', 'doctor_name', 'doctor_provider_id',
            'service', 'service_title', 'service_type',
            'custom_price', 'effective_price',
            'is_available', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AdminProviderCustomServiceSerializer(serializers.ModelSerializer):
    """Admin view of provider-created custom services."""
    provider_email = serializers.CharField(source='provider.user.email', read_only=True)
    provider_type = serializers.CharField(source='provider.provider_type', read_only=True)
    specialty_name = serializers.CharField(source='specialty.title', read_only=True, allow_null=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)

    class Meta:
        model = ProviderCustomService
        fields = [
            'id', 'provider', 'provider_email', 'provider_type',
            'title', 'title_en', 'title_ar', 'title_fr',
            'description', 'description_en', 'description_ar', 'description_fr',
            'price', 'currency', 'currency_display', 'duration_minutes',
            'specialty', 'specialty_name',
            'is_active', 'is_home_service', 'is_online_available',
            'image', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
