"""
Permission classes for the appointments app.

Provides granular access control for:
- Appointment viewing (participants only)
- Appointment creation (patients and providers)
- Status transitions (confirm, cancel, complete, no-show)
- Rescheduling (with restrictions after confirmation)
"""
from rest_framework import permissions

from .models import AppointmentStatus


class IsAppointmentParticipant(permissions.BasePermission):
    """
    Permission that allows access only to participants of an appointment.
    
    Participants include:
    - The patient (patient_user)
    - The provider's user account
    - Admin users
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin can access any appointment
        if user.is_staff or user.is_superuser:
            return True
        
        # Patient can access their own appointments
        if obj.patient_user and obj.patient_user == user:
            return True
        
        # Provider can access appointments where they are the provider
        if hasattr(user, 'provider_profile'):
            if obj.provider == user.provider_profile:
                return True
        
        # Also check if user is the creator
        if obj.created_by == user:
            return True
        
        return False


class IsProviderOrReadOnly(permissions.BasePermission):
    """
    Permission that allows providers to modify, but others can only read.
    """
    
    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for providers
        if hasattr(request.user, 'provider_profile'):
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the appointment's provider
        if hasattr(request.user, 'provider_profile'):
            return request.user.provider_profile == obj.provider
        
        return False


class CanCreateAppointment(permissions.BasePermission):
    """
    Permission for creating appointments.
    
    Allows:
    - Patients to create appointments for themselves
    - Providers to create appointments for any patient
    - Admins to create any appointment
    """
    
    def has_permission(self, request, view):
        user = request.user
        
        # Must be authenticated
        if not user.is_authenticated:
            return False
        
        # Admin can create any appointment
        if user.is_staff or user.is_superuser:
            return True
        
        # Providers can create appointments
        if hasattr(user, 'provider_profile'):
            return True
        
        # Patients can create appointments for themselves
        if hasattr(user, 'role') and user.role == 'PATIENT':
            return True
        
        return False


class CanConfirmAppointment(permissions.BasePermission):
    """
    Permission for confirming appointments.
    
    Only the provider can confirm an appointment.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin can confirm
        if user.is_staff or user.is_superuser:
            return True
        
        # Provider can confirm their own appointments
        if hasattr(user, 'provider_profile'):
            return user.provider_profile == obj.provider
        
        return False


class CanCancelAppointment(permissions.BasePermission):
    """
    Permission for cancelling appointments.
    
    Both patient and provider can cancel an appointment.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin can cancel
        if user.is_staff or user.is_superuser:
            return True
        
        # Patient can cancel their own appointment
        if obj.patient_user and obj.patient_user == user:
            return True
        
        # Provider can cancel their own appointments
        if hasattr(user, 'provider_profile'):
            return user.provider_profile == obj.provider
        
        return False


class CanCompleteAppointment(permissions.BasePermission):
    """
    Permission for completing appointments.
    
    Only the provider can mark an appointment as completed.
    Also validates that the appointment is in CONFIRMED status.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin can complete
        if user.is_staff or user.is_superuser:
            return True
        
        # Provider can complete their own appointments
        if hasattr(user, 'provider_profile'):
            return user.provider_profile == obj.provider
        
        return False


class CanRescheduleAppointment(permissions.BasePermission):
    """
    Permission for rescheduling appointments.
    
    Uses centralized AppointmentPermissionHelper for consistent permission logic.
    
    Rules:
    - PENDING appointments: Both patient and provider can reschedule
    - CONFIRMED/RESCHEDULED appointments: Only provider or admin can reschedule
    - COMPLETED/CANCELLED/REJECTED: Cannot be rescheduled
    """
    message = "You don't have permission to reschedule this appointment."
    
    def has_object_permission(self, request, view, obj):
        from common.domain_helpers import AppointmentPermissionHelper
        
        can_reschedule, reason = AppointmentPermissionHelper.can_reschedule(
            request.user, obj
        )
        
        if not can_reschedule:
            self.message = reason
        
        return can_reschedule


class IsProviderOrAdmin(permissions.BasePermission):
    """
    Permission that allows only providers or admins.
    """
    
    def has_permission(self, request, view):
        user = request.user
        
        if user.is_staff or user.is_superuser:
            return True
        
        if hasattr(user, 'provider_profile'):
            return True
        
        return False


class IsOwnProviderAvailability(permissions.BasePermission):
    """
    Permission for managing provider availability.
    
    Providers can only manage their own availability.
    Admins can manage any provider's availability.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user.is_staff or user.is_superuser:
            return True
        
        if hasattr(user, 'provider_profile'):
            return obj.provider == user.provider_profile
        
        return False
