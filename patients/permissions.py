"""
Permission classes for Patient Records app.
"""
from rest_framework import permissions

from accounts.models import User
from common.enums import UserRole
from patients.models import PatientRecord, ProviderPatientAccess


class IsVerifiedProvider(permissions.BasePermission):
    """
    Permission check: User must be an authenticated, approved provider.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if not request.user.can_login:
            return False
        
        if request.user.role != UserRole.PROVIDER:
            return False
        
        # Check if provider profile exists and is approved
        try:
            provider = request.user.provider_profile
            return provider.is_approved
        except Exception:
            return False


class CanAccessPatientRecord(permissions.BasePermission):
    """
    Object-level permission: Check if user can access a specific patient record.
    
    Access is granted if:
    - User is the linked patient
    - User is a provider who created the record
    - User is a provider with explicit access granted
    - User is an admin
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admins can access everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Patients can only access their own linked records
        if user.role == UserRole.PATIENT:
            return obj.linked_user == user
        
        # Providers check
        if user.role == UserRole.PROVIDER:
            try:
                provider = user.provider_profile
                
                # Creator has access
                if obj.created_by_provider == provider:
                    return True
                
                # Check explicit access grant
                if ProviderPatientAccess.objects.filter(
                    provider=provider,
                    patient_record=obj
                ).exists():
                    return True
                
            except Exception:
                return False
        
        return False


class CanModifyPatientRecord(permissions.BasePermission):
    """
    Permission check: Can user modify a patient record?
    
    Modification allowed if:
    - User is the provider who created the record
    - User is a provider with FULL access
    - User is an admin
    """
    
    def has_object_permission(self, request, view, obj):
        # Safe methods don't need modify permission
        if request.method in permissions.SAFE_METHODS:
            return True
        
        user = request.user
        
        # Admins can modify everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Patients cannot modify records directly (only via account update)
        if user.role == UserRole.PATIENT:
            return False
        
        # Providers check
        if user.role == UserRole.PROVIDER:
            try:
                provider = user.provider_profile
                
                # Creator can modify
                if obj.created_by_provider == provider:
                    return True
                
                # Check for FULL access
                access = ProviderPatientAccess.objects.filter(
                    provider=provider,
                    patient_record=obj,
                    access_level='FULL'
                ).first()
                
                return access is not None
                
            except Exception:
                return False
        
        return False


class CanLinkPatientAccount(permissions.BasePermission):
    """
    Permission check: Can user link a patient account?
    
    Only authenticated patients can link accounts.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PATIENT and
            request.user.can_login
        )
