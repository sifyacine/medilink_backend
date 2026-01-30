"""Comprehensive profile serializers for GET /me/ and PATCH /me/ endpoints."""
from rest_framework import serializers

from django.contrib.contenttypes.models import ContentType

from accounts.models import User
from common.enums import UserRole
from address.models import Address
from address.serializers import AddressSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Comprehensive user profile serializer for GET /me/ endpoint.
    Aggregates user data with role-specific profile information.
    """
    # Basic user fields
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    account_status = serializers.CharField(read_only=True)
    account_status_display = serializers.CharField(source='get_account_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    
    # Verification and status
    email_verified = serializers.BooleanField(read_only=True)
    email_verified_at = serializers.DateTimeField(read_only=True)
    
    # Profile completion
    profile_completed = serializers.BooleanField(read_only=True)
    profile_completion_percentage = serializers.IntegerField(read_only=True)
    
    # Login tracking
    last_login = serializers.DateTimeField(read_only=True)
    last_login_ip = serializers.IPAddressField(read_only=True)
    
    # Timestamps
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Role-specific profile data
    provider_profile = serializers.SerializerMethodField()
    patient_profile = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()
    provider_type = serializers.SerializerMethodField()
    provider_type_display = serializers.SerializerMethodField()
    # Backwards-compatible subtype alias so frontends can
    # read a generic `subtype` field (e.g. DOCTOR, CLINIC).
    subtype = serializers.SerializerMethodField()
    subtype_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'role',
            'role_display',
            'account_status',
            'account_status_display',
            'is_active',
            'is_staff',
            'email_verified',
            'email_verified_at',
            'profile_completed',
            'profile_completion_percentage',
            'last_login',
            'last_login_ip',
            'created_at',
            'updated_at',
            'provider_profile',
            'patient_profile',
            'addresses',
            'provider_type',
            'provider_type_display',
            'subtype',
            'subtype_display',
        ]
    
    def get_provider_profile(self, obj):
        """Get provider-specific profile data if user is a provider."""
        if obj.role != UserRole.PROVIDER:
            return None
        
        try:
            provider = obj.provider_profile
            from providers.serializers.status import ProviderStatusSerializer
            # Propagate serializer context (especially request) so that any
            # nested ImageField/FileField can build fully-qualified URLs.
            profile_data = ProviderStatusSerializer(provider, context=self.context).data
            
            # Add provider subtype data based on provider_type
            from common.enums import ProviderType
            provider_type = provider.provider_type
            profile_data['provider_type'] = provider_type
            
            try:
                label = ProviderType(provider_type).label if provider_type in ProviderType.values else provider.get_provider_type_display()
            except Exception:
                label = provider.get_provider_type_display()

            if label:
                profile_data['provider_type_display'] = label

            try:
                if provider_type == ProviderType.DOCTOR:
                    from providers.serializers.doctor import DoctorSerializer
                    profile_data['doctor'] = DoctorSerializer(
                        provider.doctor_profile,
                        context=self.context,
                    ).data
                elif provider_type == ProviderType.NURSE:
                    from providers.serializers.nurse import NurseSerializer
                    profile_data['nurse'] = NurseSerializer(
                        provider.nurse_profile,
                        context=self.context,
                    ).data
                elif provider_type == ProviderType.CLINIC:
                    from providers.serializers.clinic import ClinicSerializer
                    profile_data['clinic'] = ClinicSerializer(
                        provider.clinic_profile,
                        context=self.context,
                    ).data
                elif provider_type == ProviderType.LABORATORY:
                    from providers.serializers.laboratory import LaboratorySerializer
                    profile_data['laboratory'] = LaboratorySerializer(
                        provider.laboratory_profile,
                        context=self.context,
                    ).data
                elif provider_type == ProviderType.SELLER:
                    from providers.serializers.seller import SellerSerializer
                    profile_data['seller'] = SellerSerializer(
                        provider.seller_profile,
                        context=self.context,
                    ).data
                elif provider_type == ProviderType.VTC:
                    from providers.serializers.vtc import VTCSerializer
                    profile_data['vtc'] = VTCSerializer(
                        provider.vtc_profile,
                        context=self.context,
                    ).data
            except Exception:
                # Subtype profile doesn't exist yet
                pass
            
            return profile_data
        except Exception:
            return None
    
    def get_patient_profile(self, obj):
        """Get patient-specific profile data if user is a patient."""
        if obj.role != UserRole.PATIENT:
            return None
        
        profile_data = {
            'is_patient': True,
            'has_patient_record': False,
            'patient_record': None,
        }
        
        # Check if this user has a linked PatientRecord
        try:
            if hasattr(obj, 'patient_record') and obj.patient_record:
                from patients.serializers import PatientRecordSerializer
                patient_record = obj.patient_record
                profile_data['has_patient_record'] = True
                profile_data['patient_record'] = PatientRecordSerializer(
                    patient_record,
                    context=self.context,
                ).data
        except Exception:
            pass
        
        return profile_data

    def get_addresses(self, obj):
        """Return all addresses attached to this user account.

        This is primarily used by the frontend on the `/api/auth/me/` screen
        so profile pages can display and manage account-level addresses.

        For providers, this aggregates addresses linked directly to the user
        as well as to their provider/doctor/nurse profiles, mirroring the
        behavior of the AddressViewSet queryset.
        """
        user_content_type = ContentType.objects.get_for_model(User)

        # Addresses attached directly to the user account
        addresses_qs = Address.objects.filter(
            content_type=user_content_type,
            object_id=obj.id,
        )

        # If user is also a provider, include related provider/doctor/nurse addresses
        if hasattr(obj, "provider_profile"):
            try:
                provider = obj.provider_profile
                provider_ct = ContentType.objects.get_for_model(provider.__class__)
                provider_addresses = Address.objects.filter(
                    content_type=provider_ct,
                    object_id=provider.id,
                )

                doctor_addresses = Address.objects.none()
                nurse_addresses = Address.objects.none()

                if hasattr(provider, "doctor_profile"):
                    doctor = provider.doctor_profile
                    doctor_ct = ContentType.objects.get_for_model(doctor.__class__)
                    doctor_addresses = Address.objects.filter(
                        content_type=doctor_ct,
                        object_id=doctor.id,
                    )

                if hasattr(provider, "nurse_profile"):
                    nurse = provider.nurse_profile
                    nurse_ct = ContentType.objects.get_for_model(nurse.__class__)
                    nurse_addresses = Address.objects.filter(
                        content_type=nurse_ct,
                        object_id=nurse.id,
                    )

                addresses_qs = (
                    addresses_qs
                    | provider_addresses
                    | doctor_addresses
                    | nurse_addresses
                ).distinct()
            except Exception:
                pass

        addresses_qs = addresses_qs.order_by("-is_primary", "-updated_at")

        return AddressSerializer(addresses_qs, many=True).data

    def get_provider_type(self, obj):
        """Return provider type value for provider users."""
        if obj.role != UserRole.PROVIDER:
            return None

        try:
            provider = obj.provider_profile
            return getattr(provider, 'provider_type', None)
        except Exception:
            return None

    def get_provider_type_display(self, obj):
        """Return a human-readable provider type label."""
        if obj.role != UserRole.PROVIDER:
            return None

        try:
            provider = obj.provider_profile
        except Exception:
            return None

        try:
            from common.enums import ProviderType

            provider_type = getattr(provider, 'provider_type', None)
            if provider_type and provider_type in ProviderType.values:
                return ProviderType(provider_type).label
        except Exception:
            pass

        return provider.get_provider_type_display()

    # ------------------------------------------------------------------
    # Backwards-compatible subtype helpers
    # ------------------------------------------------------------------

    def get_subtype(self, obj):
        """Expose provider subtype as a generic `subtype` field.

        This mirrors `provider_type` for provider users so that
        clients expecting a `subtype` key (e.g. DOCTOR, CLINIC)
        continue to work.
        """
        return self.get_provider_type(obj)

    def get_subtype_display(self, obj):
        """Human readable label for the subtype (e.g. Doctor)."""
        return self.get_provider_type_display(obj)


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for PATCH /me/ endpoint.
    Only allows updating safe, user-editable fields.
    All sensitive fields (role, status, verification, etc.) are read-only.
    """
    # Email is read-only (use separate email change endpoint if needed)
    email = serializers.EmailField(read_only=True)
    
    # These fields are NEVER editable by users
    role = serializers.CharField(read_only=True)
    account_status = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    email_verified = serializers.BooleanField(read_only=True)
    email_verified_at = serializers.DateTimeField(read_only=True)
    # Allow users to update their own profile completion flags.
    # These are safe, per-user indicators and do not grant privileges.
    profile_completed = serializers.BooleanField(required=False)
    profile_completion_percentage = serializers.IntegerField(required=False, min_value=0, max_value=100)
    last_login = serializers.DateTimeField(read_only=True)
    last_login_ip = serializers.IPAddressField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # ------------------------------------------------------------------
    # Provider profile editable fields (for current user only)
    # ------------------------------------------------------------------
    # These do not live on the User model, but on the
    # provider subtype models (Doctor, Nurse, Clinic, etc.).
    # They are declared here so /api/auth/me/ can accept them
    # and route updates to the appropriate profile instance.

    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    biography = serializers.CharField(required=False, allow_blank=True)
    years_of_experience = serializers.IntegerField(required=False, min_value=0, max_value=100)
    is_available = serializers.BooleanField(required=False)
    is_home_service_available = serializers.BooleanField(required=False)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    profile_image = serializers.ImageField(required=False, allow_null=True)

    # Sensitive provider fields that must NOT be changed directly
    # by the user. If these are sent, we return a clear error
    # asking the user to contact support.
    license_number = serializers.CharField(required=False, allow_blank=True, write_only=True)
    degree_document = serializers.FileField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email',
            'role',
            'account_status',
            'is_active',
            'is_staff',
            'is_superuser',
            'email_verified',
            'email_verified_at',
            'profile_completed',
            'profile_completion_percentage',
            'last_login',
            'last_login_ip',
            'created_at',
            'updated_at',
            # Provider profile editable fields exposed via /api/auth/me/
            'first_name',
            'last_name',
            'gender',
            'biography',
            'years_of_experience',
            'is_available',
            'is_home_service_available',
            'phone_number',
            'profile_image',
            # Sensitive provider fields are declared as write-only and
            # explicitly blocked in `update()` with a clear message.
            'license_number',
            'degree_document',
        ]
    
    def update(self, instance, validated_data):
        """
        Update user instance.
        Note: Most fields are read-only, so this mainly handles edge cases.
        Role-specific profile updates should be handled in separate endpoints.
        """
        # Pull out provider-related fields so they are not applied
        # to the User instance directly.
        provider_fields = {}
        for field in [
            'first_name',
            'last_name',
            'gender',
            'biography',
            'years_of_experience',
            'is_available',
            'is_home_service_available',
            'phone_number',
            'profile_image',
            'license_number',
            'degree_document',
        ]:
            if field in validated_data:
                provider_fields[field] = validated_data.pop(field)

        # Block direct changes to sensitive provider fields
        sensitive_errors = {}
        if provider_fields.get('license_number') not in (None, ''):
            sensitive_errors['license_number'] = [
                'This field cannot be changed from the app. Please contact support.',
            ]
        if provider_fields.get('degree_document') is not None:
            sensitive_errors['degree_document'] = [
                'This field cannot be changed from the app. Please contact support.',
            ]
        if sensitive_errors:
            raise serializers.ValidationError(sensitive_errors)

        # Update timestamp tracking on the User instance
        if 'request' in self.context:
            instance.updated_by = self.context['request'].user
        
        # Apply remaining (safe) fields to the User instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If no provider-related fields were supplied, we're done
        if not provider_fields:
            return instance

        # Provider-related updates are only valid for provider accounts
        if not instance.is_provider:
            errors = {
                key: ['This field is only available for provider accounts.']
                for key in provider_fields.keys()
            }
            raise serializers.ValidationError(errors)

        # Resolve the concrete provider subtype profile
        try:
            provider = instance.provider_profile
        except Exception:
            raise serializers.ValidationError(
                {
                    'detail': 'Provider profile is not configured for this account. Please contact support.',
                }
            )

        try:
            from common.enums import ProviderType
        except Exception:
            ProviderType = None

        provider_type = getattr(provider, 'provider_type', None)
        profile_obj = None

        try:
            if ProviderType and provider_type == ProviderType.DOCTOR:
                profile_obj = provider.doctor_profile
                subtype = 'doctor'
            elif ProviderType and provider_type == ProviderType.NURSE:
                profile_obj = provider.nurse_profile
                subtype = 'nurse'
            elif ProviderType and provider_type == ProviderType.CLINIC:
                profile_obj = provider.clinic_profile
                subtype = 'clinic'
            elif ProviderType and provider_type == ProviderType.LABORATORY:
                profile_obj = provider.laboratory_profile
                subtype = 'laboratory'
            elif ProviderType and provider_type == ProviderType.SELLER:
                profile_obj = provider.seller_profile
                subtype = 'seller'
            elif ProviderType and provider_type == ProviderType.VTC:
                profile_obj = provider.vtc_profile
                subtype = 'vtc'
            else:
                profile_obj = None
                subtype = None
        except Exception:
            profile_obj = None
            subtype = None

        if profile_obj is None:
            raise serializers.ValidationError(
                {
                    'detail': 'Profile for this provider type is not available. Please contact support.',
                }
            )

        field_errors = {}

        # Helper to assign a field if it exists on the profile
        def set_field(field_name, model_attr=None):
            nonlocal field_errors
            if field_name not in provider_fields:
                return
            value = provider_fields[field_name]
            target_attr = model_attr or field_name
            if not hasattr(profile_obj, target_attr):
                field_errors[field_name] = [
                    'This field is not editable for your provider type.',
                ]
                return
            setattr(profile_obj, target_attr, value)

        # Doctor / Nurse personal fields
        if subtype in ('doctor', 'nurse'):
            set_field('first_name')
            set_field('last_name')
            set_field('gender')
            set_field('biography')
            set_field('years_of_experience')
            set_field('is_available')
            set_field('is_home_service_available')
            set_field('profile_image')
            set_field('phone_number')

        # Organization-style providers (clinic, lab, seller, vtc)
        if subtype in ('clinic', 'laboratory', 'seller', 'vtc'):
            set_field('phone_number')
            set_field('is_available')
            # For clinics we treat `profile_image` as logo if provided
            if subtype == 'clinic':
                set_field('profile_image', model_attr='logo')

        if field_errors:
            # Do not persist partial changes if there are field-level errors
            raise serializers.ValidationError(field_errors)

        # Persist provider profile changes
        try:
            profile_obj.save()
        except Exception:
            raise serializers.ValidationError(
                {
                    'detail': 'Could not update provider profile at this time. Please try again or contact support.',
                }
            )

        return instance
