"""
Business logic services for accounts.
"""
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from accounts.models import User
from common.enums import UserRole

User = get_user_model()


def create_patient_user(email, password):
    """
    Create a new patient user.
    
    Args:
        email: User email address
        password: User password
        
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
    
    # Check if user already exists
    try:
        existing_user = User.objects.get(email=email_lower)
        if existing_user.role == UserRole.PROVIDER:
            try:
                provider = existing_user.provider_profile
                return existing_user, provider, False
            except Provider.DoesNotExist:
                provider = Provider.objects.create(
                    user=existing_user,
                    provider_type=provider_type,
                    status='PENDING',
                )
                return existing_user, provider, False
        raise ValueError(f'User with email {email_lower} already exists with role {existing_user.role}.')
    except User.DoesNotExist:
        pass
    
    # Create new user
    user = User.objects.create_user(
        email=email_lower,
        password=password,
        role=UserRole.PROVIDER,
        is_active=True,
    )
    
    from django.db import transaction
    with transaction.atomic():
        provider = Provider.objects.create(
            user=user,
            provider_type=provider_type,
            status='PENDING',
        )
        
        # Extract common fields
        first_name = extra_data.get('first_name', '')
        last_name = extra_data.get('last_name', '')
        
        # Subtype-specific creation
        if provider_type == 'DOCTOR':
            from providers.models.doctor import Doctor
            Doctor.objects.create(
                provider=provider,
                first_name=first_name,
                last_name=last_name,
                license_number=extra_data.get('license_number', ''),
                degree_document=extra_data.get('degree_document'),
            )
        elif provider_type == 'NURSE':
            from providers.models.nurse import Nurse
            Nurse.objects.create(
                provider=provider,
                first_name=first_name,
                last_name=last_name,
                license_number=extra_data.get('license_number', ''),
                degree_document=extra_data.get('degree_document'),
                entrepreneur_card_front=extra_data.get('entrepreneur_card_front'),
                entrepreneur_card_back=extra_data.get('entrepreneur_card_back'),
            )
        elif provider_type == 'CLINIC':
            from providers.models.clinic import Clinic
            Clinic.objects.create(
                provider=provider,
                clinic_name=extra_data.get('clinic_name', ''),
                license_number=extra_data.get('license_number', ''),
                license_document=extra_data.get('degree_document'), # Map degree_document to license if applicable
            )
        elif provider_type == 'LABORATORY':
            from providers.models.laboratory import Laboratory
            Laboratory.objects.create(
                provider=provider,
                lab_name=extra_data.get('lab_name', ''),
                license_number=extra_data.get('license_number', ''),
                license_document=extra_data.get('degree_document'),
            )
        elif provider_type == 'SELLER':
            from providers.models.seller import Seller
            Seller.objects.create(
                provider=provider,
                business_name=extra_data.get('business_name', ''),
                tax_id=extra_data.get('tax_id', ''),
                business_license=extra_data.get('degree_document'),
            )
        elif provider_type == 'VTC':
            from providers.models.vtc import VTC
            VTC.objects.create(
                provider=provider,
                company_name=extra_data.get('company_name', ''),
                license_number=extra_data.get('license_number', ''),
                transport_license=extra_data.get('degree_document'),
            )

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
