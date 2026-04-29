"""
Admin serializers for provider verification and management.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from providers.models import Provider
from providers.models.statuses import ProviderStatusHistory
from common.enums import ProviderType


# ---------------------------------------------------------------------------
# Status history
# ---------------------------------------------------------------------------

class ProviderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializes a single status-change audit entry."""
    old_status_display = serializers.CharField(source='get_old_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True, allow_null=True)

    class Meta:
        model = ProviderStatusHistory
        fields = [
            'id',
            'old_status',
            'old_status_display',
            'new_status',
            'new_status_display',
            'changed_by_email',
            'reason',
            'created_at',
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# List serializer (compact, for the providers table in the admin panel)
# ---------------------------------------------------------------------------

class ProviderListSerializer(serializers.ModelSerializer):
    """Compact provider row for the admin panel list/table view."""
    email = serializers.EmailField(source='user.email', read_only=True)
    account_status = serializers.CharField(source='user.account_status', read_only=True)
    provider_type_display = serializers.CharField(source='get_provider_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)

    # Human-readable name that works across all provider types
    name = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Provider
        fields = [
            'id',
            'email',
            'account_status',
            'provider_type',
            'provider_type_display',
            'name',
            'profile_image',
            'status',
            'status_display',
            'refusal_reason',
            'approved_at',
            'approved_by_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_name(self, obj):
        try:
            if obj.provider_type == ProviderType.DOCTOR:
                d = obj.doctor_profile
                return f"Dr. {d.first_name} {d.last_name}".strip()
            if obj.provider_type == ProviderType.NURSE:
                n = obj.nurse_profile
                return f"{n.first_name} {n.last_name}".strip()
            if obj.provider_type == ProviderType.CLINIC:
                return obj.clinic_profile.clinic_name
            if obj.provider_type == ProviderType.LABORATORY:
                return obj.laboratory_profile.lab_name
            if obj.provider_type == ProviderType.SELLER:
                return obj.seller_profile.business_name
            if obj.provider_type == ProviderType.VTC:
                return obj.vtc_profile.company_name
        except Exception:
            pass
        return obj.user.email

    def get_profile_image(self, obj):
        request = self.context.get('request')
        image = None
        try:
            if obj.provider_type == ProviderType.DOCTOR:
                image = obj.doctor_profile.profile_image or None
            elif obj.provider_type == ProviderType.NURSE:
                image = obj.nurse_profile.profile_image or None
            elif obj.provider_type == ProviderType.CLINIC:
                image = obj.clinic_profile.logo or None
        except Exception:
            pass
        if image:
            return request.build_absolute_uri(image.url) if request else image.url
        return None


# ---------------------------------------------------------------------------
# Sub-profile inline serializers (admin sees documents too)
# ---------------------------------------------------------------------------

class _AdminDoctorInlineSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    gender = serializers.CharField(read_only=True)
    date_of_birth = serializers.DateField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    license_number = serializers.CharField(read_only=True)
    years_of_experience = serializers.IntegerField(read_only=True)
    biography = serializers.CharField(read_only=True)
    consultation_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    home_visit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    online_consultation_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    currency = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    is_home_service_available = serializers.BooleanField(read_only=True)
    degree_document = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    def _build_url(self, field):
        request = self.context.get('request')
        if field and hasattr(field, 'url'):
            return request.build_absolute_uri(field.url) if request else field.url
        return None

    def get_degree_document(self, obj):
        return self._build_url(obj.degree_document)

    def get_profile_image(self, obj):
        return self._build_url(obj.profile_image)


class _AdminNurseInlineSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    gender = serializers.CharField(read_only=True)
    date_of_birth = serializers.DateField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    license_number = serializers.CharField(read_only=True)
    certification = serializers.CharField(read_only=True)
    years_of_experience = serializers.IntegerField(read_only=True)
    biography = serializers.CharField(read_only=True)
    service_area_km = serializers.IntegerField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    is_home_service_available = serializers.BooleanField(read_only=True)
    profile_image = serializers.SerializerMethodField()
    degree_document = serializers.SerializerMethodField()
    entrepreneur_card_front = serializers.SerializerMethodField()
    entrepreneur_card_back = serializers.SerializerMethodField()
    entrepreneur_card_pdf = serializers.SerializerMethodField()

    def _build_url(self, field):
        request = self.context.get('request')
        if field and hasattr(field, 'url'):
            return request.build_absolute_uri(field.url) if request else field.url
        return None

    def get_profile_image(self, obj):
        return self._build_url(obj.profile_image)

    def get_degree_document(self, obj):
        return self._build_url(obj.degree_document)

    def get_entrepreneur_card_front(self, obj):
        return self._build_url(getattr(obj, 'entrepreneur_card_front', None))

    def get_entrepreneur_card_back(self, obj):
        return self._build_url(getattr(obj, 'entrepreneur_card_back', None))

    def get_entrepreneur_card_pdf(self, obj):
        return self._build_url(getattr(obj, 'entrepreneur_card_pdf', None))


class _AdminClinicInlineSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    clinic_name = serializers.CharField(read_only=True)
    license_number = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    website = serializers.URLField(read_only=True)
    description = serializers.CharField(read_only=True)
    number_of_beds = serializers.IntegerField(read_only=True)
    has_emergency_services = serializers.BooleanField(read_only=True)
    is_24_hours = serializers.BooleanField(read_only=True)
    outpatient_capacity_per_day = serializers.IntegerField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    logo = serializers.SerializerMethodField()
    license_document = serializers.SerializerMethodField()

    def _build_url(self, field):
        request = self.context.get('request')
        if field and hasattr(field, 'url'):
            return request.build_absolute_uri(field.url) if request else field.url
        return None

    def get_logo(self, obj):
        return self._build_url(obj.logo)

    def get_license_document(self, obj):
        return self._build_url(obj.license_document)


class _AdminLaboratoryInlineSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    lab_name = serializers.CharField(read_only=True)
    license_number = serializers.CharField(read_only=True)
    accreditation = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    website = serializers.URLField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    license_document = serializers.SerializerMethodField()
    accreditation_document = serializers.SerializerMethodField()

    def _build_url(self, field):
        request = self.context.get('request')
        if field and hasattr(field, 'url'):
            return request.build_absolute_uri(field.url) if request else field.url
        return None

    def get_license_document(self, obj):
        return self._build_url(obj.license_document)

    def get_accreditation_document(self, obj):
        return self._build_url(getattr(obj, 'accreditation_document', None))


class _AdminSellerInlineSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    business_name = serializers.CharField(read_only=True)
    tax_id = serializers.CharField(read_only=True)
    business_type = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    website = serializers.URLField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    business_license = serializers.SerializerMethodField()
    tax_certificate = serializers.SerializerMethodField()

    def _build_url(self, field):
        request = self.context.get('request')
        if field and hasattr(field, 'url'):
            return request.build_absolute_uri(field.url) if request else field.url
        return None

    def get_business_license(self, obj):
        return self._build_url(getattr(obj, 'business_license', None))

    def get_tax_certificate(self, obj):
        return self._build_url(getattr(obj, 'tax_certificate', None))


class _AdminVTCInlineSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    company_name = serializers.CharField(read_only=True)
    license_number = serializers.CharField(read_only=True)
    fleet_size = serializers.IntegerField(read_only=True)
    vehicle_types = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    website = serializers.URLField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    transport_license = serializers.SerializerMethodField()
    insurance_certificate = serializers.SerializerMethodField()

    def _build_url(self, field):
        request = self.context.get('request')
        if field and hasattr(field, 'url'):
            return request.build_absolute_uri(field.url) if request else field.url
        return None

    def get_transport_license(self, obj):
        return self._build_url(getattr(obj, 'transport_license', None))

    def get_insurance_certificate(self, obj):
        return self._build_url(getattr(obj, 'insurance_certificate', None))


# ---------------------------------------------------------------------------
# Full detail serializer (admin panel provider detail page)
# ---------------------------------------------------------------------------

class AdminProviderDetailSerializer(serializers.ModelSerializer):
    """
    Full provider detail for the admin panel.
    Includes user account info, sub-profile with all documents,
    addresses, social links, and approval metadata.
    """
    # User account fields
    email = serializers.EmailField(source='user.email', read_only=True)
    account_status = serializers.CharField(source='user.account_status', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    user_created_at = serializers.DateTimeField(source='user.created_at', read_only=True)

    # Provider status display
    provider_type_display = serializers.CharField(source='get_provider_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Approval metadata
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)

    # Type-specific sub-profiles (only the matching one will be non-null)
    doctor = serializers.SerializerMethodField()
    nurse = serializers.SerializerMethodField()
    clinic = serializers.SerializerMethodField()
    laboratory = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    vtc = serializers.SerializerMethodField()

    # Related data
    addresses = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    recent_status_history = serializers.SerializerMethodField()

    class Meta:
        model = Provider
        fields = [
            'id',
            # User
            'email',
            'account_status',
            'is_active',
            'user_created_at',
            # Provider base
            'provider_type',
            'provider_type_display',
            'status',
            'status_display',
            'refusal_reason',
            'approved_at',
            'approved_by_email',
            'daily_appointment_limit',
            'created_at',
            'updated_at',
            # Sub-profiles
            'doctor',
            'nurse',
            'clinic',
            'laboratory',
            'seller',
            'vtc',
            # Related
            'addresses',
            'social_links',
            'recent_status_history',
        ]
        read_only_fields = fields

    def get_doctor(self, obj):
        if obj.provider_type != ProviderType.DOCTOR:
            return None
        try:
            return _AdminDoctorInlineSerializer(obj.doctor_profile, context=self.context).data
        except Exception:
            return None

    def get_nurse(self, obj):
        if obj.provider_type != ProviderType.NURSE:
            return None
        try:
            return _AdminNurseInlineSerializer(obj.nurse_profile, context=self.context).data
        except Exception:
            return None

    def get_clinic(self, obj):
        if obj.provider_type != ProviderType.CLINIC:
            return None
        try:
            return _AdminClinicInlineSerializer(obj.clinic_profile, context=self.context).data
        except Exception:
            return None

    def get_laboratory(self, obj):
        if obj.provider_type != ProviderType.LABORATORY:
            return None
        try:
            return _AdminLaboratoryInlineSerializer(obj.laboratory_profile, context=self.context).data
        except Exception:
            return None

    def get_seller(self, obj):
        if obj.provider_type != ProviderType.SELLER:
            return None
        try:
            return _AdminSellerInlineSerializer(obj.seller_profile, context=self.context).data
        except Exception:
            return None

    def get_vtc(self, obj):
        if obj.provider_type != ProviderType.VTC:
            return None
        try:
            return _AdminVTCInlineSerializer(obj.vtc_profile, context=self.context).data
        except Exception:
            return None

    def get_addresses(self, obj):
        try:
            from django.db.models import Q
            from accounts.models import User
            from address.models import Address
            from address.serializers import AddressSerializer

            provider_ct = ContentType.objects.get_for_model(Provider)
            user_ct = ContentType.objects.get_for_model(User)
            addresses = Address.objects.filter(
                Q(content_type=provider_ct, object_id=obj.id) |
                Q(content_type=user_ct, object_id=obj.user_id)
            ).order_by('-is_primary', 'created_at')
            return AddressSerializer(addresses, many=True).data
        except Exception:
            return []

    def get_social_links(self, obj):
        try:
            from social_media.models import SocialMediaLink
            from social_media.serializers import SocialMediaLinkSerializer
            ct = ContentType.objects.get_for_model(Provider)
            links = SocialMediaLink.objects.filter(
                content_type=ct,
                object_id=obj.id,
            ).order_by('display_order', 'platform')
            return SocialMediaLinkSerializer(links, many=True, context=self.context).data
        except Exception:
            return []

    def get_recent_status_history(self, obj):
        try:
            history = obj.status_history.select_related('changed_by').order_by('-created_at')[:10]
            return ProviderStatusHistorySerializer(history, many=True).data
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Action input serializers
# ---------------------------------------------------------------------------

class ProviderRefuseSerializer(serializers.Serializer):
    """Validates the body for the refuse action."""
    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        min_length=10,
        help_text='Reason for refusing the provider (minimum 10 characters)',
    )

    def validate_reason(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError('Refusal reason must be at least 10 characters.')
        return value


class ProviderSuspendSerializer(serializers.Serializer):
    """Optional body for the suspend action."""
    reason = serializers.CharField(required=False, allow_blank=True, default='')
