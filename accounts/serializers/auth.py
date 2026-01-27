"""
Authentication serializers for signup and login.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from common.enums import UserRole

User = get_user_model()


class PatientRegisterSerializer(serializers.Serializer):
    """Serializer for patient registration."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True
    )
    
    def validate_email(self, value):
        """Check if email is already registered."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()
    
    def validate(self, attrs):
        """Validate password confirmation and per-type required fields."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })

        provider_type = attrs.get('provider_type')

        # Per-role minimal required professional info at signup
        # Doctor: normal identity + license and degree document
        if provider_type == 'DOCTOR':
            required_fields = [
                'first_name',
                'last_name',
                'phone_number',
                'license_number',
                'degree_document',
            ]
            errors = {}
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = 'This field is required for doctor signup.'
            if errors:
                raise serializers.ValidationError(errors)

        # Nurse: degree + entrepreneur card front/back as a start
        elif provider_type == 'NURSE':
            required_fields = [
                'first_name',
                'last_name',
                'phone_number',
                'license_number',
                'degree_document',
                'entrepreneur_card_front',
                'entrepreneur_card_back',
            ]
            errors = {}
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = 'This field is required for nurse signup.'
            if errors:
                raise serializers.ValidationError(errors)

        # Clinic: license number and basic clinic info
        elif provider_type == 'CLINIC':
            required_fields = [
                'clinic_name',
                'license_number',
                'phone_number',
            ]
            errors = {}
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = 'This field is required for clinic signup.'
            if errors:
                raise serializers.ValidationError(errors)

        # Laboratory: license number and basic lab info
        elif provider_type == 'LABORATORY':
            required_fields = [
                'lab_name',
                'license_number',
                'phone_number',
            ]
            errors = {}
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = 'This field is required for laboratory signup.'
            if errors:
                raise serializers.ValidationError(errors)

        # VTC: license number and basic company info
        elif provider_type == 'VTC':
            required_fields = [
                'company_name',
                'license_number',
                'phone_number',
            ]
            errors = {}
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = 'This field is required for VTC signup.'
            if errors:
                raise serializers.ValidationError(errors)

        # Seller/Pharmacy: basic business identity
        elif provider_type == 'SELLER':
            required_fields = [
                'business_name',
                'phone_number',
                'tax_id',
            ]
            errors = {}
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = 'This field is required for seller signup.'
            if errors:
                raise serializers.ValidationError(errors)

        return attrs
    
    def create(self, validated_data):
        """Create a new patient user."""
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=UserRole.PATIENT,
            is_active=True,
        )
        return user


class ProviderRegisterSerializer(serializers.Serializer):
    """
    Serializer for provider registration.
    
    Handles idempotency: If provider already exists, returns existing provider.
    If user exists with different role, raises validation error.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True
    )
    provider_type = serializers.ChoiceField(
        choices=[
            ('DOCTOR', 'Doctor'),
            ('NURSE', 'Nurse'),
            ('CLINIC', 'Clinic'),
            ('LABORATORY', 'Laboratory'),
            ('VTC', 'Healthcare VTC'),
            ('SELLER', 'Seller'),
        ],
        required=True
    )
    
    # Professional Information (Combined into registration)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    
    # Provider-specific Fields
    license_number = serializers.CharField(required=False, allow_blank=True)
    degree_document = serializers.FileField(required=False, allow_null=True)
    
    # Nurse-specific Fields
    entrepreneur_card_front = serializers.ImageField(required=False, allow_null=True)
    entrepreneur_card_back = serializers.ImageField(required=False, allow_null=True)
    
    # Clinic/Lab/VTC/Seller Specific
    clinic_name = serializers.CharField(required=False, allow_blank=True)
    lab_name = serializers.CharField(required=False, allow_blank=True)
    company_name = serializers.CharField(required=False, allow_blank=True)
    business_name = serializers.CharField(required=False, allow_blank=True)
    tax_id = serializers.CharField(required=False, allow_blank=True)
    
    def validate_email(self, value):
        """
        Validate email and check for existing users.
        
        Allows re-registration if user is already a provider (idempotency).
        Blocks if user exists with different role.
        """
        value_lower = value.lower()
        try:
            existing_user = User.objects.get(email__iexact=value_lower)
            if existing_user.role != UserRole.PROVIDER:
                raise serializers.ValidationError(
                    f'User with this email already exists with role {existing_user.role}. '
                    'Cannot create provider account.'
                )
            # User is already a provider - allow re-registration (idempotent)
        except User.DoesNotExist:
            pass  # New user - OK
        return value_lower
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs


class CustomRegisterSerializer(serializers.Serializer):
    """
    Custom registration serializer for dj-rest-auth compatibility.
    This is used by dj-rest-auth but we'll use our own endpoints.
    """
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()
    
    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return attrs
    
    def get_cleaned_data(self):
        return {
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
        }
    
    def save(self, request):
        """
        Save user with role enforcement.
        
        IMPORTANT: Role is hardcoded to PATIENT to prevent admin self-registration.
        Admin users must be created via Django admin or programmatically by superuser.
        """
        cleaned_data = self.get_cleaned_data()
        
        # Enforce PATIENT role - prevent admin self-registration
        user = User.objects.create_user(
            email=cleaned_data['email'],
            password=cleaned_data['password1'],
            role=UserRole.PATIENT,  # Hardcoded - cannot be changed via API
        )
        return user
