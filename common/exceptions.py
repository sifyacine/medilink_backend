"""
Custom exceptions for the Medilink platform.

Provides domain-specific exceptions with consistent error messaging
and HTTP status code mapping for the API.
"""
from rest_framework import status


class MedilinkException(Exception):
    """
    Base exception for all Medilink-specific errors.
    
    Provides:
    - Consistent error message structure
    - HTTP status code mapping
    - Error code for frontend handling
    """
    default_message = "An error occurred."
    default_code = "error"
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, message=None, code=None, status_code=None, details=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to API response dictionary."""
        response = {
            'success': False,
            'error': self.message,
            'code': self.code,
        }
        if self.details:
            response['details'] = self.details
        return response


# =============================================================================
# APPOINTMENT EXCEPTIONS
# =============================================================================

class AppointmentException(MedilinkException):
    """Base exception for appointment-related errors."""
    default_code = "appointment_error"


class InvalidStatusTransitionError(AppointmentException):
    """Raised when an invalid status transition is attempted."""
    default_message = "Invalid appointment status transition."
    default_code = "invalid_status_transition"
    
    def __init__(self, from_status, to_status, allowed_transitions=None):
        message = f"Cannot transition from {from_status} to {to_status}."
        if allowed_transitions:
            message += f" Allowed: {', '.join(sorted(allowed_transitions))}"
        
        super().__init__(
            message=message,
            details={
                'from_status': from_status,
                'to_status': to_status,
                'allowed_transitions': list(allowed_transitions) if allowed_transitions else []
            }
        )


class TimeSlotUnavailableError(AppointmentException):
    """Raised when a requested time slot is not available."""
    default_message = "The requested time slot is not available."
    default_code = "time_slot_unavailable"
    
    def __init__(self, reason=None):
        message = reason or self.default_message
        super().__init__(message=message)


class DoubleBookingError(AppointmentException):
    """Raised when a booking would create a scheduling conflict."""
    default_message = "This time slot is already booked."
    default_code = "double_booking"


class AppointmentNotModifiableError(AppointmentException):
    """Raised when trying to modify an appointment that cannot be changed."""
    default_message = "This appointment cannot be modified."
    default_code = "not_modifiable"
    
    def __init__(self, status):
        message = f"Cannot modify appointment with status: {status}"
        super().__init__(
            message=message,
            details={'current_status': status}
        )


class BookingWindowError(AppointmentException):
    """Raised when booking is outside allowed time window."""
    default_message = "Booking is outside the allowed time window."
    default_code = "booking_window_error"


# =============================================================================
# PATIENT EXCEPTIONS
# =============================================================================

class PatientException(MedilinkException):
    """Base exception for patient-related errors."""
    default_code = "patient_error"


class PatientRecordNotFoundError(PatientException):
    """Raised when a patient record is not found."""
    default_message = "Patient record not found."
    default_code = "patient_not_found"
    default_status_code = status.HTTP_404_NOT_FOUND


class LinkingTokenInvalidError(PatientException):
    """Raised when a patient linking token is invalid."""
    default_message = "Invalid or expired linking token."
    default_code = "invalid_linking_token"


class LinkingTokenAlreadyUsedError(PatientException):
    """Raised when a patient linking token has already been used."""
    default_message = "This linking token has already been used."
    default_code = "token_already_used"


class PatientAlreadyLinkedError(PatientException):
    """Raised when trying to link an already-linked patient record."""
    default_message = "This patient record is already linked to an account."
    default_code = "already_linked"


# =============================================================================
# PROVIDER EXCEPTIONS
# =============================================================================

class ProviderException(MedilinkException):
    """Base exception for provider-related errors."""
    default_code = "provider_error"


class ProviderNotVerifiedError(ProviderException):
    """Raised when a non-verified provider attempts a restricted action."""
    default_message = "Provider must be verified to perform this action."
    default_code = "provider_not_verified"
    default_status_code = status.HTTP_403_FORBIDDEN


class ProviderNotFoundError(ProviderException):
    """Raised when a provider is not found."""
    default_message = "Provider not found."
    default_code = "provider_not_found"
    default_status_code = status.HTTP_404_NOT_FOUND


# =============================================================================
# PERMISSION EXCEPTIONS
# =============================================================================

class PermissionException(MedilinkException):
    """Base exception for permission-related errors."""
    default_code = "permission_error"
    default_status_code = status.HTTP_403_FORBIDDEN


class AccessDeniedError(PermissionException):
    """Raised when user doesn't have access to a resource."""
    default_message = "You don't have permission to access this resource."
    default_code = "access_denied"


class NotParticipantError(PermissionException):
    """Raised when user is not a participant in an appointment."""
    default_message = "You are not a participant in this appointment."
    default_code = "not_participant"


# =============================================================================
# PRESCRIPTION EXCEPTIONS
# =============================================================================

class PrescriptionException(MedilinkException):
    """Base exception for prescription-related errors."""
    default_code = "prescription_error"


class PrescriptionNotModifiableError(PrescriptionException):
    """Raised when trying to modify a non-draft prescription."""
    default_message = "Only draft prescriptions can be modified."
    default_code = "prescription_not_modifiable"


class AppointmentNotCompletedError(PrescriptionException):
    """Raised when trying to create prescription for incomplete appointment."""
    default_message = "Prescription can only be issued for completed appointments."
    default_code = "appointment_not_completed"


# =============================================================================
# VALIDATION EXCEPTIONS
# =============================================================================

class ValidationException(MedilinkException):
    """Base exception for validation errors."""
    default_code = "validation_error"
    default_status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def __init__(self, field_errors=None, message=None):
        """
        Initialize with field-specific errors.
        
        Args:
            field_errors: Dict mapping field names to error messages
            message: General error message
        """
        self.field_errors = field_errors or {}
        super().__init__(
            message=message or "Validation failed.",
            details={'fields': self.field_errors}
        )
