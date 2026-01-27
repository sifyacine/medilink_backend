"""
Permission classes for Medical Records app.
"""
from rest_framework import permissions
from accounts.models import User
from common.enums import UserRole


class IsPatientOwnerOrAuthorizedProvider(permissions.BasePermission):
    """
    Permission check for medical records.
    
    Allows access if:
    - User is the patient who owns the record, OR
    - User is an authorized provider (approved status), OR
    - User is an admin
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access medical records."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins can always access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Patients can access their own records
        if request.user.role == UserRole.PATIENT:
            return True
        
        # Providers must be approved to access records
        if request.user.role == UserRole.PROVIDER:
            try:
                provider = request.user.provider_profile
                from common.enums import ProviderStatus
                return provider.status == ProviderStatus.APPROVED
            except Exception:
                return False
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access a specific medical record."""
        # Admins can access all records
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Patients can access their own records
        if request.user.role == UserRole.PATIENT:
            return obj.patient == request.user
        
        # Approved providers can access all patient records
        if request.user.role == UserRole.PROVIDER:
            try:
                provider = request.user.provider_profile
                from common.enums import ProviderStatus
                if provider.status == ProviderStatus.APPROVED:
                    # Providers can access records of any patient
                    return obj.patient.role == UserRole.PATIENT
            except Exception:
                pass
        
        return False


class CanCreateMedicalRecord(permissions.BasePermission):
    """
    Permission check for creating medical records.
    
    Allows creation if:
    - User is a patient creating their own record, OR
    - User is an approved provider creating a record for a patient, OR
    - User is an admin
    """
    
    def has_permission(self, request, view):
        """Check if user can create medical records."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role == UserRole.ADMIN:
            return True
        
        if request.user.role == UserRole.PATIENT:
            return True
        
        if request.user.role == UserRole.PROVIDER:
            try:
                provider = request.user.provider_profile
                from common.enums import ProviderStatus
                return provider.status == ProviderStatus.APPROVED
            except Exception:
                return False
        
        return False


class CanModifyMedicalRecord(permissions.BasePermission):
    """
    Permission check for modifying medical records.
    
    Patients can modify their own records but with restrictions on provider-created fields.
    Providers can modify records they created or any patient record.
    Admins can modify any record.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can modify a specific medical record."""
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admins can modify all records
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Patients can modify their own records
        if request.user.role == UserRole.PATIENT:
            if obj.patient == request.user:
                # Additional check: patients have limited rights on provider-created records
                # This is enforced in the serializer
                return True
            return False
        
        # Approved providers can modify any patient record
        if request.user.role == UserRole.PROVIDER:
            try:
                provider = request.user.provider_profile
                from common.enums import ProviderStatus
                if provider.status == ProviderStatus.APPROVED:
                    return obj.patient.role == UserRole.PATIENT
            except Exception:
                pass
        
        return False


class CanDeleteMedicalRecord(permissions.BasePermission):
    """
    Permission check for deleting medical records.
    
    Patients can delete their own records (soft delete via is_active).
    Providers can delete records they created.
    Admins can delete any record.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can delete a specific medical record."""
        # Admins can delete all records
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Patients can delete their own records
        if request.user.role == UserRole.PATIENT:
            return obj.patient == request.user
        
        # Providers can delete records they created
        if request.user.role == UserRole.PROVIDER:
            if obj.created_by == request.user:
                try:
                    provider = request.user.provider_profile
                    from common.enums import ProviderStatus
                    return provider.status == ProviderStatus.APPROVED
                except Exception:
                    pass
        
        return False
