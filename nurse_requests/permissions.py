from rest_framework import permissions
from common.enums import UserRole


class IsPatient(permissions.BasePermission):
    """
    Permission to check if user is a patient.
    """
    message = "Only patients can perform this action."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PATIENT
        )


class IsNurse(permissions.BasePermission):
    """
    Permission to check if user is a nurse provider.
    Checks both provider_profile existence and provider_type.
    """
    message = "Only nurse providers can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has a provider_profile
        if not hasattr(request.user, 'provider_profile'):
            self.message = "User does not have a provider profile. Please contact support."
            return False
        
        provider = request.user.provider_profile
        
        # Check if provider_type is NURSE
        if provider.provider_type != 'NURSE':
            self.message = f"User is a {provider.provider_type} provider, not a nurse provider."
            return False
        
        # Check if nurse_profile exists
        if not hasattr(provider, 'nurse_profile'):
            self.message = "Nurse profile not found. Please contact support."
            return False
        
        return True


class IsRequestOwner(permissions.BasePermission):
    """
    Permission to check if user is the owner of the request.
    """
    message = "You can only access your own requests."

    def has_object_permission(self, request, view, obj):
        # Check if user is the patient_user or linked to patient_record
        if obj.patient_user:
            return obj.patient_user == request.user
        elif obj.patient_record and obj.patient_record.linked_user:
            return obj.patient_record.linked_user == request.user
        return False


class CanModifyRequest(permissions.BasePermission):
    """
    Permission to check if request can be modified based on its status.
    """
    message = "This request cannot be modified in its current state."

    def has_object_permission(self, request, view, obj):
        # Only allow modifications on requests that are not completed/cancelled
        modifiable_statuses = ['CREATED', 'SEARCHING', 'NURSE_RESPONDED', 'PATIENT_DECISION']
        return obj.status in modifiable_statuses
