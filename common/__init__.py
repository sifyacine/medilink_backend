"""
Common utilities and shared components for the Medilink platform.

This package provides:
- utils: Centralized utility functions (patient/provider helpers, response formatting)
- domain_helpers: Business logic helpers (status transitions, permission helpers)
- exceptions: Custom domain exceptions
- exception_handlers: Custom DRF exception handler for consistent API responses
- i18n: Internationalization utilities (multilingual content support)
- permissions: Base permission classes
- enums: Centralized enumerations
- validators: Custom validators
"""

# Convenience imports for commonly used utilities
from common.utils import (
    get_patient_display_name,
    get_patient_email,
    get_patient_phone,
    get_patient_info_dict,
    get_provider_display_name,
    get_provider_info_dict,
    success_response,
    error_response,
)

from common.domain_helpers import (
    AppointmentStatusTransition,
    AppointmentPermissionHelper,
    BookingWindowValidator,
)

from common.exceptions import (
    MedilinkException,
    AppointmentException,
    InvalidStatusTransitionError,
    TimeSlotUnavailableError,
    DoubleBookingError,
    PatientException,
    ProviderException,
    PermissionException,
)

from common.i18n import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    get_language_from_request,
    get_localized_field,
    get_all_translations,
    MultilingualSerializerMixin,
    LocalizedFieldsMixin,
    LocalizedCharField,
    TranslationsField,
)

__all__ = [
    # Utils
    'get_patient_display_name',
    'get_patient_email',
    'get_patient_phone',
    'get_patient_info_dict',
    'get_provider_display_name',
    'get_provider_info_dict',
    'success_response',
    'error_response',
    # Domain helpers
    'AppointmentStatusTransition',
    'AppointmentPermissionHelper',
    'BookingWindowValidator',
    # Exceptions
    'MedilinkException',
    'AppointmentException',
    'InvalidStatusTransitionError',
    'TimeSlotUnavailableError',
    'DoubleBookingError',
    'PatientException',
    'ProviderException',
    'PermissionException',
    # i18n
    'SUPPORTED_LANGUAGES',
    'DEFAULT_LANGUAGE',
    'get_language_from_request',
    'get_localized_field',
    'get_all_translations',
    'MultilingualSerializerMixin',
    'LocalizedFieldsMixin',
    'LocalizedCharField',
    'TranslationsField',
]
