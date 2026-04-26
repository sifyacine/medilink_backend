"""
Business logic services for accounts.
"""
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.db import transaction

from accounts.models import User
from common.enums import UserRole

User = get_user_model()


def _apply_identity_fields(user, extra_data):
    """Apply shared identity fields to the auth user when provided."""
    updated_fields = []
    for field in ('first_name', 'last_name', 'phone_number'):
        if field in extra_data:
            value = extra_data.get(field)
            if getattr(user, field, None) != value:
                setattr(user, field, value)
                updated_fields.append(field)

    if updated_fields:
        user.save(update_fields=updated_fields)


def _ensure_provider_subtype(provider, provider_type, extra_data):
    """Create the subtype profile if it does not already exist."""
    if provider_type == 'DOCTOR':
        from providers.models.doctor import Doctor

        if hasattr(provider, 'doctor_profile'):
            return provider.doctor_profile

        # Convert empty strings to None for license_number to avoid unique constraint violation
        license_number = extra_data.get('license_number', '')
        if not license_number or license_number.strip() == '':
            license_number = None

        return Doctor.objects.create(
            provider=provider,
            first_name=extra_data.get('first_name', ''),
            last_name=extra_data.get('last_name', ''),
            license_number=license_number,
            degree_document=extra_data.get('degree_document'),
        )

    if provider_type == 'NURSE':
        from providers.models.nurse import Nurse

        if hasattr(provider, 'nurse_profile'):
            return provider.nurse_profile

        # Convert empty strings to None for license_number to avoid unique constraint violation
        license_number = extra_data.get('license_number', '')
        if not license_number or license_number.strip() == '':
            license_number = None

        return Nurse.objects.create(
            provider=provider,
            first_name=extra_data.get('first_name', ''),
            last_name=extra_data.get('last_name', ''),
            phone_number=extra_data.get('phone_number', ''),
            license_number=license_number,
            degree_document=extra_data.get('degree_document'),
            entrepreneur_card_front=extra_data.get('entrepreneur_card_front'),
            entrepreneur_card_back=extra_data.get('entrepreneur_card_back'),
            entrepreneur_card_pdf=extra_data.get('entrepreneur_card_pdf'),
        )

    if provider_type == 'CLINIC':
        from providers.models.clinic import Clinic

        if hasattr(provider, 'clinic_profile'):
            return provider.clinic_profile

        # Convert empty strings to None for license_number to avoid unique constraint violation
        license_number = extra_data.get('license_number', '')
        if not license_number or license_number.strip() == '':
            license_number = None

        return Clinic.objects.create(
            provider=provider,
            clinic_name=extra_data.get('clinic_name', ''),
            license_number=license_number,
            license_document=extra_data.get('degree_document'),
        )

    if provider_type == 'LABORATORY':
        from providers.models.laboratory import Laboratory

        if hasattr(provider, 'laboratory_profile'):
            return provider.laboratory_profile

        # Convert empty strings to None for license_number to avoid unique constraint violation
        license_number = extra_data.get('license_number', '')
        if not license_number or license_number.strip() == '':
            license_number = None

        return Laboratory.objects.create(
            provider=provider,
            lab_name=extra_data.get('lab_name', ''),
            license_number=license_number,
            license_document=extra_data.get('degree_document'),
        )

    if provider_type == 'SELLER':
        from providers.models.seller import Seller

        if hasattr(provider, 'seller_profile'):
            return provider.seller_profile

        return Seller.objects.create(
            provider=provider,
            business_name=extra_data.get('business_name', ''),
            tax_id=extra_data.get('tax_id', ''),
            business_license=extra_data.get('degree_document'),
        )

    if provider_type == 'VTC':
        from providers.models.vtc import VTC

        if hasattr(provider, 'vtc_profile'):
            return provider.vtc_profile

        # Convert empty strings to None for license_number to avoid unique constraint violation
        license_number = extra_data.get('license_number', '')
        if not license_number or license_number.strip() == '':
            license_number = None

        return VTC.objects.create(
            provider=provider,
            company_name=extra_data.get('company_name', ''),
            license_number=license_number,
            transport_license=extra_data.get('degree_document'),
        )

    return None


def create_patient_user(email, password, first_name='', last_name='', phone_number=''):
    """
    Create a new patient user.
    
    Args:
        email: User email address
        password: User password
        first_name: Patient first name (optional)
        last_name: Patient last name (optional)
        phone_number: Patient phone number (optional)
        
    Returns:
        User instance
        
    Raises:
        ValueError: If user already exists
    """
    email_lower = email.lower()
    
    # Prevent duplicate registration
    if User.objects.filter(email=email_lower).exists():
        raise ValueError(f'User with email {email_lower} already exists.')
    
    user = User.objects.create_user(
        email=email_lower,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        role=UserRole.PATIENT,
        is_active=True,
    )
    # Initialize profile completion (may remain 0 until more data exists)
    try:
        user.recalculate_profile_completion()
    except Exception:
        pass
    return user


def create_admin_user(email, password, created_by):
    """
    Create a new admin user.
    
    IMPORTANT: Only superusers can create admin users.
    This prevents self-registration as admin.
    
    Args:
        email: User email address
        password: User password
        created_by: User instance creating the admin (must be superuser)
        
    Returns:
        User instance
        
    Raises:
        ValueError: If creator is not superuser or user already exists
    """
    if not created_by.is_superuser:
        raise ValueError('Only superusers can create admin users.')
    
    email_lower = email.lower()
    
    if User.objects.filter(email=email_lower).exists():
        raise ValueError(f'User with email {email_lower} already exists.')
    
    user = User.objects.create_user(
        email=email_lower,
        password=password,
        role=UserRole.ADMIN,
        is_active=True,
        is_staff=True,
    )
    return user


def create_provider_user(email, password, provider_type, **extra_data):
    """
    Create a new provider user and profile with professional details.
    
    Args:
        email: User email address
        password: User password
        provider_type: Type of provider
        **extra_data: Additional profile data (first_name, license_number, files, etc.)
        
    Returns:
        tuple: (User instance, Provider instance, is_new: bool)
    """
    from providers.models import Provider
    
    email_lower = email.lower()
    extra_data = dict(extra_data)
    
    # Check if user already exists
    try:
        existing_user = User.objects.get(email=email_lower)
        if existing_user.role == UserRole.PROVIDER:
            with transaction.atomic():
                try:
                    provider = existing_user.provider_profile
                except Provider.DoesNotExist:
                    provider = Provider.objects.create(
                        user=existing_user,
                        provider_type=provider_type,
                        status='PENDING',
                    )

                if provider.provider_type != provider_type:
                    raise ValueError(
                        f'User with email {email_lower} already exists as {provider.provider_type}. '
                        'Cannot create a different provider type.'
                    )

                _apply_identity_fields(existing_user, extra_data)
                _ensure_provider_subtype(provider, provider_type, extra_data)
            return existing_user, provider, False
        raise ValueError(f'User with email {email_lower} already exists with role {existing_user.role}.')
    except User.DoesNotExist:
        pass
    
    # Create new user
    with transaction.atomic():
        user = User.objects.create_user(
            email=email_lower,
            password=password,
            role=UserRole.PROVIDER,
            is_active=True,
            first_name=extra_data.get('first_name', ''),
            last_name=extra_data.get('last_name', ''),
            phone_number=extra_data.get('phone_number', ''),
        )

        provider = Provider.objects.create(
            user=user,
            provider_type=provider_type,
            status='PENDING',
        )
        _ensure_provider_subtype(provider, provider_type, extra_data)

    # After creating the provider and subtype profile, compute completion
    try:
        user.recalculate_profile_completion()
    except Exception:
        pass
    
    return user, provider, True
  # New user and provider


def get_or_create_auth_token(user):
    """
    Get or create authentication token for user.
    
    Args:
        user: User instance
        
    Returns:
        Token instance
    """
    token, created = Token.objects.get_or_create(user=user)
    return token
