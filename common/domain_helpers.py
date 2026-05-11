"""
Centralized domain helpers for Medilink business logic.

This module provides domain-specific helper classes that encapsulate
complex business rules and ensure consistency across the codebase.
"""
from typing import Tuple, Set, Dict, Optional
from django.core.exceptions import ValidationError


class AppointmentStatusTransition:
    """
    Centralized appointment status transition manager.
    
    Defines all valid status transitions and provides validation.
    This ensures status changes are consistent across all endpoints
    (views, services, signals, etc.)
    
    Status Flow:
        PENDING -> CONFIRMED (provider accepts)
        PENDING -> REJECTED (provider rejects)
        PENDING -> CANCELLED (patient/provider cancels)
        PENDING -> RESCHEDULED (patient/provider reschedules)
        
        CONFIRMED -> COMPLETED (after appointment time)
        CONFIRMED -> NO_SHOW (patient doesn't show up)
        CONFIRMED -> CANCELLED (patient/provider cancels)
        CONFIRMED -> RESCHEDULED (reschedule confirmed appointment)
        
        RESCHEDULED -> CONFIRMED (provider confirms rescheduled time)
        RESCHEDULED -> CANCELLED (cancel rescheduled appointment)
        RESCHEDULED -> RESCHEDULED (reschedule again)
        
        COMPLETED, CANCELLED, REJECTED, NO_SHOW -> (terminal states, no transitions)
    """
    
    # Valid status transitions: {from_status: {to_statuses}}
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        'PENDING': {'CONFIRMED', 'REJECTED', 'CANCELLED', 'RESCHEDULED'},
        'CONFIRMED': {'COMPLETED', 'NO_SHOW', 'CANCELLED', 'RESCHEDULED'},
        'RESCHEDULED': {'CONFIRMED', 'CANCELLED', 'RESCHEDULED', 'COMPLETED', 'NO_SHOW'},
        'REJECTED': set(),  # Terminal state
        'CANCELLED': set(),  # Terminal state
        'COMPLETED': set(),  # Terminal state
        'NO_SHOW': set(),  # Terminal state
    }
    
    # Statuses that allow patient actions
    PATIENT_ACTIONABLE: Set[str] = {'PENDING', 'CONFIRMED', 'RESCHEDULED'}
    
    # Statuses that allow provider actions
    PROVIDER_ACTIONABLE: Set[str] = {'PENDING', 'CONFIRMED', 'RESCHEDULED'}
    
    # Terminal (final) statuses
    TERMINAL_STATUSES: Set[str] = {'COMPLETED', 'CANCELLED', 'REJECTED', 'NO_SHOW'}
    
    # Statuses considered "active" (counts toward provider's scheduled appointments)
    ACTIVE_STATUSES: Set[str] = {'PENDING', 'CONFIRMED', 'RESCHEDULED'}
    
    # Statuses that should be excluded from conflict checking
    NON_CONFLICTING_STATUSES: Set[str] = {'CANCELLED', 'REJECTED', 'NO_SHOW'}
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """
        Check if a status transition is valid.
        
        Args:
            from_status: Current appointment status
            to_status: Target appointment status
            
        Returns:
            True if transition is valid, False otherwise
        """
        valid_targets = cls.VALID_TRANSITIONS.get(from_status, set())
        return to_status in valid_targets
    
    @classmethod
    def validate_transition(cls, from_status: str, to_status: str) -> None:
        """
        Validate a status transition, raising ValidationError if invalid.
        
        Args:
            from_status: Current appointment status
            to_status: Target appointment status
            
        Raises:
            ValidationError: If transition is not valid
        """
        if not cls.can_transition(from_status, to_status):
            if from_status in cls.TERMINAL_STATUSES:
                raise ValidationError(
                    f"Cannot change status of {from_status.lower()} appointment. "
                    f"This is a terminal state."
                )
            valid_targets = cls.VALID_TRANSITIONS.get(from_status, set())
            if valid_targets:
                raise ValidationError(
                    f"Cannot transition from {from_status} to {to_status}. "
                    f"Valid transitions: {', '.join(sorted(valid_targets))}"
                )
            else:
                raise ValidationError(
                    f"Cannot change status from {from_status}. No transitions allowed."
                )
    
    @classmethod
    def get_allowed_transitions(cls, current_status: str) -> Set[str]:
        """
        Get all allowed target statuses from the current status.
        
        Args:
            current_status: Current appointment status
            
        Returns:
            Set of valid target status strings
        """
        return cls.VALID_TRANSITIONS.get(current_status, set()).copy()
    
    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Check if a status is terminal (no further transitions allowed)."""
        return status in cls.TERMINAL_STATUSES
    
    @classmethod
    def is_active(cls, status: str) -> bool:
        """Check if a status is considered active (scheduled/upcoming)."""
        return status in cls.ACTIVE_STATUSES
    
    @classmethod
    def can_patient_act(cls, status: str) -> bool:
        """Check if patient can perform actions on appointment with this status."""
        return status in cls.PATIENT_ACTIONABLE
    
    @classmethod
    def can_provider_act(cls, status: str) -> bool:
        """Check if provider can perform actions on appointment with this status."""
        return status in cls.PROVIDER_ACTIONABLE
    
    @classmethod
    def causes_conflict(cls, status: str) -> bool:
        """
        Check if an appointment with this status should block the time slot.
        
        Used in double-booking prevention logic.
        """
        return status not in cls.NON_CONFLICTING_STATUSES


class AppointmentPermissionHelper:
    """
    Helper class for appointment permission checks.
    
    Centralizes permission logic to avoid duplication across
    permission classes and views.
    """
    
    @staticmethod
    def is_appointment_participant(user, appointment) -> bool:
        """
        Check if user is a participant in the appointment.
        
        Participants include:
        - The patient (patient_user)
        - The provider's user account
        - The appointment creator
        - Admin users
        """
        if not user or not user.is_authenticated:
            return False
        
        # Admin always has access
        if user.is_staff or user.is_superuser:
            return True
        
        # Patient can access their own appointments
        if appointment.patient_user and appointment.patient_user == user:
            return True
        
        # Provider can access appointments where they are the provider
        if hasattr(user, 'provider_profile'):
            if appointment.provider == user.provider_profile:
                return True
        
        # Creator can access
        if appointment.created_by == user:
            return True
        
        return False
    
    @staticmethod
    def can_confirm(user, appointment) -> Tuple[bool, str]:
        """
        Check if user can confirm the appointment.
        
        Returns:
            Tuple of (can_confirm, reason_if_not)
        """
        if appointment.status != 'PENDING':
            return False, f"Can only confirm PENDING appointments, current status: {appointment.status}"
        
        # Only provider or admin can confirm
        if user.is_staff or user.is_superuser:
            return True, ""
        
        if hasattr(user, 'provider_profile') and user.provider_profile == appointment.provider:
            return True, ""
        
        return False, "Only the provider can confirm this appointment"
    
    @staticmethod
    def can_cancel(user, appointment) -> Tuple[bool, str]:
        """
        Check if user can cancel the appointment.
        
        Returns:
            Tuple of (can_cancel, reason_if_not)
        """
        if AppointmentStatusTransition.is_terminal(appointment.status):
            return False, f"Cannot cancel {appointment.status.lower()} appointment"
        
        # Admin can always cancel
        if user.is_staff or user.is_superuser:
            return True, ""
        
        # Patient can cancel their own appointment
        if appointment.patient_user and appointment.patient_user == user:
            return True, ""
        
        # Provider can cancel their appointments
        if hasattr(user, 'provider_profile') and user.provider_profile == appointment.provider:
            return True, ""
        
        return False, "You don't have permission to cancel this appointment"
    
    @staticmethod
    def can_complete(user, appointment) -> Tuple[bool, str]:
        """
        Check if user can mark the appointment as completed.
        
        Returns:
            Tuple of (can_complete, reason_if_not)
        """
        if appointment.status != 'CONFIRMED':
            return False, f"Can only complete CONFIRMED appointments, current status: {appointment.status}"
        
        # Only provider or admin can complete
        if user.is_staff or user.is_superuser:
            return True, ""
        
        if hasattr(user, 'provider_profile') and user.provider_profile == appointment.provider:
            return True, ""
        
        return False, "Only the provider can complete this appointment"
    
    @staticmethod
    def can_reschedule(user, appointment) -> Tuple[bool, str]:
        """
        Check if user can reschedule the appointment.
        
        Returns:
            Tuple of (can_reschedule, reason_if_not)
        """
        allowed_statuses = {'PENDING', 'CONFIRMED', 'RESCHEDULED'}
        
        if appointment.status not in allowed_statuses:
            return False, f"Cannot reschedule {appointment.status.lower()} appointment"
        
        # Admin can always reschedule
        if user.is_staff or user.is_superuser:
            return True, ""
        
        # Provider can reschedule any reschedulable appointment
        if hasattr(user, 'provider_profile') and user.provider_profile == appointment.provider:
            return True, ""
        
        # Patient can only reschedule PENDING appointments
        if appointment.patient_user and appointment.patient_user == user:
            from appointments.models import AppointmentStatus
            if appointment.status == AppointmentStatus.PENDING:
                return True, ""
            return False, "Patients can only reschedule pending appointments. Contact the provider."
        
        return False, "You don't have permission to reschedule this appointment"


class BookingWindowValidator:
    """
    Validator for appointment booking time windows.
    
    Centralizes booking window rules for consistency.
    """
    
    # Minimum booking notice in hours
    MIN_BOOKING_NOTICE_HOURS: int = 1
    
    # Maximum advance booking in days
    MAX_ADVANCE_BOOKING_DAYS: int = 90
    
    # Minimum appointment duration in minutes
    MIN_DURATION_MINUTES: int = 5
    
    # Maximum appointment duration in minutes
    MAX_DURATION_MINUTES: int = 480  # 8 hours
    
    @classmethod
    def validate_booking_window(
        cls,
        appointment_datetime,
        current_datetime=None
    ) -> Tuple[bool, str]:
        """
        Validate that an appointment falls within the allowed booking window.
        
        Args:
            appointment_datetime: Datetime of the appointment
            current_datetime: Current datetime (for testing, defaults to now)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        from django.utils import timezone
        from datetime import timedelta
        
        if current_datetime is None:
            current_datetime = timezone.now()
        
        # Ensure timezone awareness
        if timezone.is_naive(appointment_datetime):
            appointment_datetime = timezone.make_aware(appointment_datetime)
        
        # Check minimum notice
        min_booking_time = current_datetime + timedelta(hours=cls.MIN_BOOKING_NOTICE_HOURS)
        if appointment_datetime < min_booking_time:
            return False, f"Appointments require at least {cls.MIN_BOOKING_NOTICE_HOURS} hour(s) notice."
        
        # Check maximum advance booking
        max_booking_date = current_datetime.date() + timedelta(days=cls.MAX_ADVANCE_BOOKING_DAYS)
        if appointment_datetime.date() > max_booking_date:
            return False, f"Cannot book more than {cls.MAX_ADVANCE_BOOKING_DAYS} days in advance."
        
        return True, ""
    
    @classmethod
    def validate_duration(cls, duration_minutes: int) -> Tuple[bool, str]:
        """
        Validate appointment duration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if duration_minutes < cls.MIN_DURATION_MINUTES:
            return False, f"Appointment must be at least {cls.MIN_DURATION_MINUTES} minutes."
        
        if duration_minutes > cls.MAX_DURATION_MINUTES:
            return False, f"Appointment cannot exceed {cls.MAX_DURATION_MINUTES} minutes."
        
        return True, ""
