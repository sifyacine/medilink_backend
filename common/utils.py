"""
Centralized utility functions for the Medilink platform.

This module provides shared helper functions used across multiple apps:
- Patient information helpers
- Provider information helpers  
- Response formatting helpers
- Query optimization helpers
"""
from typing import Optional, Any, Dict, List
from django.db.models import Model, Prefetch


# =============================================================================
# PATIENT UTILITIES
# =============================================================================

def get_patient_display_name(patient_user=None, patient_record=None) -> str:
    """
    Get a consistent display name for a patient.
    
    Centralizes patient name resolution logic to ensure consistency
    across appointments, prescriptions, medical records, etc.
    
    Args:
        patient_user: User model instance (patient with account)
        patient_record: PatientRecord model instance (patient without account)
        
    Returns:
        Human-readable patient name string
    """
    if patient_user:
        full_name = patient_user.get_full_name() if hasattr(patient_user, 'get_full_name') else None
        if full_name and full_name.strip():
            return full_name.strip()
        return 'A patient'
    
    if patient_record:
        first = getattr(patient_record, 'first_name', '') or ''
        last = getattr(patient_record, 'last_name', '') or ''
        full_name = f'{first} {last}'.strip()
        if full_name:
            return full_name
        return getattr(patient_record, 'patient_unique_id', str(patient_record))
    
    return 'Unknown Patient'


def get_patient_email(patient_user=None, patient_record=None) -> Optional[str]:
    """
    Get patient email address.
    
    Args:
        patient_user: User model instance
        patient_record: PatientRecord model instance
        
    Returns:
        Email string or None if not available
    """
    if patient_user:
        return getattr(patient_user, 'email', None)
    if patient_record:
        email = getattr(patient_record, 'email', None)
        return email if email else None
    return None


def get_patient_phone(patient_user=None, patient_record=None) -> Optional[str]:
    """
    Get patient phone number.
    
    Args:
        patient_user: User model instance
        patient_record: PatientRecord model instance
        
    Returns:
        Phone number string or None if not available
    """
    if patient_user:
        return getattr(patient_user, 'phone_number', None)
    if patient_record:
        return getattr(patient_record, 'phone_number', None)
    return None


def get_patient_info_dict(patient_user=None, patient_record=None) -> Dict[str, Any]:
    """
    Get complete patient info dictionary for API responses.
    
    Provides consistent patient information structure across all endpoints.
    
    Returns:
        Dictionary with patient_name, patient_email, patient_phone, patient_id
    """
    patient_id = None
    if patient_user:
        patient_id = str(patient_user.id)
    elif patient_record:
        patient_id = getattr(patient_record, 'patient_unique_id', str(patient_record.id))
    
    return {
        'patient_id': patient_id,
        'patient_name': get_patient_display_name(patient_user, patient_record),
        'patient_email': get_patient_email(patient_user, patient_record),
        'patient_phone': get_patient_phone(patient_user, patient_record),
    }


# =============================================================================
# PROVIDER UTILITIES
# =============================================================================

def get_provider_display_name(provider) -> str:
    """
    Get a consistent display name for a provider.
    
    Handles different provider types (Doctor, Nurse, Clinic, etc.)
    and returns an appropriate display name.
    
    Args:
        provider: Provider model instance
        
    Returns:
        Human-readable provider name string
    """
    if not provider:
        return 'Unknown Provider'
    
    # Try to get specific profile names
    try:
        if hasattr(provider, 'doctor_profile') and provider.doctor_profile:
            doctor = provider.doctor_profile
            first = getattr(doctor, 'first_name', '')
            last = getattr(doctor, 'last_name', '')
            if first or last:
                return f'Dr. {first} {last}'.strip()
        
        if hasattr(provider, 'nurse_profile') and provider.nurse_profile:
            nurse = provider.nurse_profile
            first = getattr(nurse, 'first_name', '')
            last = getattr(nurse, 'last_name', '')
            if first or last:
                return f'{first} {last}'.strip()
        
        if hasattr(provider, 'clinic_profile') and provider.clinic_profile:
            return getattr(provider.clinic_profile, 'clinic_name', '') or \
                   getattr(provider.clinic_profile, 'name', '')
        
        if hasattr(provider, 'laboratory_profile') and provider.laboratory_profile:
            return getattr(provider.laboratory_profile, 'lab_name', '') or \
                   getattr(provider.laboratory_profile, 'name', '')
        
        if hasattr(provider, 'vtc_profile') and provider.vtc_profile:
            return getattr(provider.vtc_profile, 'company_name', '') or \
                   getattr(provider.vtc_profile, 'name', '')
        
        if hasattr(provider, 'seller_profile') and provider.seller_profile:
            return getattr(provider.seller_profile, 'store_name', '') or \
                   getattr(provider.seller_profile, 'name', '')
        
    except Exception:
        pass
    
    # Fallback to user info
    try:
        if hasattr(provider, 'user'):
            user = provider.user
            full_name = user.get_full_name() if hasattr(user, 'get_full_name') else None
            if full_name and full_name.strip():
                return full_name.strip()
            return user.email if hasattr(user, 'email') else str(user)
    except Exception:
        pass
    
    return str(provider)


def get_provider_info_dict(provider) -> Dict[str, Any]:
    """
    Get complete provider info dictionary for API responses.
    
    Provides consistent provider information structure across all endpoints.
    
    Returns:
        Dictionary with provider_id, provider_name, provider_email, provider_type
    """
    if not provider:
        return {
            'provider_id': None,
            'provider_name': 'Unknown Provider',
            'provider_email': None,
            'provider_type': None,
        }
    
    provider_email = None
    if hasattr(provider, 'user'):
        provider_email = getattr(provider.user, 'email', None)
    
    provider_type = getattr(provider, 'provider_type', None)
    
    return {
        'provider_id': str(provider.id) if provider.id else None,
        'provider_name': get_provider_display_name(provider),
        'provider_email': provider_email,
        'provider_type': provider_type,
    }


# =============================================================================
# API RESPONSE HELPERS
# =============================================================================

def success_response(data: Any = None, message: str = None, **extra) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data payload
        message: Optional success message
        **extra: Additional fields to include
        
    Returns:
        Standardized response dictionary
    """
    response = {'success': True}
    if message:
        response['message'] = message
    if data is not None:
        response['data'] = data
    response.update(extra)
    return response


def error_response(error: str, code: str = None, details: Dict = None) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error: Error message
        code: Optional error code
        details: Optional error details dictionary
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        'success': False,
        'error': error,
    }
    if code:
        response['code'] = code
    if details:
        response['details'] = details
    return response


# =============================================================================
# QUERY OPTIMIZATION HELPERS
# =============================================================================

def get_appointment_select_related() -> List[str]:
    """
    Get standard select_related fields for appointment queries.
    
    Use this to ensure consistent query optimization across viewsets.
    
    Returns:
        List of related field names for select_related()
    """
    return [
        'provider',
        'provider__user',
        'patient_user',
        'patient_record',
        'service',
        'created_by',
        'cancelled_by',
        'clinic_address',
        'home_address',
    ]


def get_appointment_prefetch_related() -> list:
    """
    Get standard prefetch_related fields for appointment queries.

    Includes Prefetch objects for custom service pricing so serializers
    can resolve provider-specific prices without issuing per-item DB queries.

    Returns:
        List of strings and Prefetch objects for prefetch_related()
    """
    from services.models import DoctorService, NurseService

    return [
        'reminders',
        'appointment_services__service',
        Prefetch(
            'provider__doctor_profile__services',
            queryset=DoctorService.objects.select_related('service'),
            to_attr='prefetched_custom_services',
        ),
        Prefetch(
            'provider__nurse_profile__services',
            queryset=NurseService.objects.select_related('service'),
            to_attr='prefetched_custom_services',
        ),
    ]


def get_prescription_select_related() -> List[str]:
    """
    Get standard select_related fields for prescription queries.
    
    Returns:
        List of related field names for select_related()
    """
    return [
        'doctor',
        'doctor__provider',
        'doctor__provider__user',
        'patient',
        'patient_record',
        'clinic',
        'appointment',
    ]


def get_medical_record_select_related() -> List[str]:
    """
    Get standard select_related fields for medical record queries.
    
    Returns:
        List of related field names for select_related()
    """
    return [
        'patient',
        'patient_record',
        'created_by',
        'updated_by',
    ]


def get_medical_record_prefetch_related() -> List[str]:
    """
    Get standard prefetch_related fields for medical record queries.
    
    Returns:
        List of related field names for prefetch_related()
    """
    return [
        'attachments',
        'notes',
    ]
