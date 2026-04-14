"""
Permission classes for Medical Records app.
"""
from rest_framework import permissions
from accounts.models import User
from common.enums import UserRole
from django.utils import timezone


def get_record_patient_user(record):
    """Resolve the owning patient user for a medical record when available."""
    if record.patient:
        return record.patient
    if record.patient_record and record.patient_record.linked_user:
        return record.patient_record.linked_user
    return None


def has_provider_access(provider, patient=None, patient_record=None, required_access='READ_ONLY'):
    """
    Check if a provider has valid access to a patient's records.
    
    Args:
        provider: Provider instance
        patient: User instance (patient)
        patient_record: PatientRecord instance
        required_access: 'READ_ONLY', 'FULL', or 'LIMITED'
    
    Returns:
        bool: True if provider has valid access
    """
    from medical_record.models import ProviderAccess
    from patients.models import ProviderPatientAccess

    # Resolve patient_record from patient when possible
    if not patient_record and patient and hasattr(patient, 'patient_record'):
        patient_record = patient.patient_record

    # Check new medical_record.ProviderAccess grants
    if patient:
        try:
            access = ProviderAccess.objects.get(
                provider=provider,
                patient=patient,
                is_active=True
            )

            if access.expires_at and timezone.now() > access.expires_at:
                return False

            if required_access == 'FULL' and access.access_type != 'FULL':
                return False

            return True
        except ProviderAccess.DoesNotExist:
            pass

    # Backward compatibility for legacy patient record access grants
    if patient_record:
        try:
            access = ProviderPatientAccess.objects.get(
                provider=provider,
                patient_record=patient_record,
            )
            if required_access == 'FULL' and access.access_level != 'FULL':
                return False
            return True
        except ProviderPatientAccess.DoesNotExist:
            pass

    return False


class IsPatientOwnerOrAuthorizedProvider(permissions.BasePermission):
    """
    Permission check for medical records.
    
    Allows access if:
    - User is the patient who owns the record, OR
    - User is an authorized provider with valid access grant, OR
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
            record_owner = get_record_patient_user(obj)
            return record_owner == request.user
        
        # Providers need explicit access grant
        if request.user.role == UserRole.PROVIDER:
            try:
                provider = request.user.provider_profile
                from common.enums import ProviderStatus
                if provider.status != ProviderStatus.APPROVED:
                    return False
                
                # Check if provider has access to this patient
                # If they created the record, they have access
                if obj.created_by == request.user:
                    return True
                
                # Otherwise check ProviderAccess
                return has_provider_access(provider, obj.patient, obj.patient_record)
            except Exception:
                pass
        
        return False


class CanCreateMedicalRecord(permissions.BasePermission):
    """
    Permission check for creating medical records.
    
    Allows creation if:
    - User is a patient creating their own record, OR
    - User is an approved provider creating a record for a patient they have access to, OR
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
    Providers can modify records they created or records of patients they have FULL access to.
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
            record_owner = get_record_patient_user(obj)
            if record_owner == request.user:
                return True
            return False
        
        # Providers need FULL access or to have created the record
        if request.user.role == UserRole.PROVIDER:
            try:
                provider = request.user.provider_profile
                from common.enums import ProviderStatus
                if provider.status != ProviderStatus.APPROVED:
                    return False
                
                # Can always modify records they created
                if obj.created_by == request.user:
                    return True
                
                # Need FULL access to modify other records
                return has_provider_access(provider, obj.patient, obj.patient_record, 'FULL')
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
            record_owner = get_record_patient_user(obj)
            return record_owner == request.user
        
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


class CanManageProviderAccess(permissions.BasePermission):
    """
    Permission check for managing provider access grants.
    
    Patients can grant/revoke access to their own records.
    Admins can manage access for any patient.
    """
    
    def has_permission(self, request, view):
        """Check if user can manage provider access."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role == UserRole.ADMIN:
            return True
        
        if request.user.role == UserRole.PATIENT:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Check if user can manage a specific access grant."""
        if request.user.role == UserRole.ADMIN:
            return True
        
        if request.user.role == UserRole.PATIENT:
            return obj.patient == request.user
        
        return False
