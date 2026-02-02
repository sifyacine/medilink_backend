"""
Base permission classes for the Medilink platform.
"""
from rest_framework import permissions

from accounts.models import User
from common.enums import UserRole, UserAccountStatus


class IsPatient(permissions.BasePermission):
    """Permission check: User must be authenticated and have PATIENT role."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PATIENT and
            request.user.can_login
        )


class IsProvider(permissions.BasePermission):
    """Permission check: User must be authenticated and have PROVIDER role."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PROVIDER and
            request.user.can_login
        )


class IsVerifiedProvider(permissions.BasePermission):
    """
    Permission check: User must be authenticated, have PROVIDER role,
    and have VERIFIED status.
    
    This is the centralized guard that prevents PENDING/REFUSED providers
    from accessing protected resources.
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
        except User.provider_profile.RelatedObjectDoesNotExist:
            return False


class IsAdmin(permissions.BasePermission):
    """Permission check: User must be authenticated and have ADMIN role."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.ADMIN and
            request.user.can_login
        )


class IsProviderOrReadOnly(permissions.BasePermission):
    """
    Permission check: Providers can write, others can only read.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PROVIDER and
            request.user.can_login
        )


class IsNurse(permissions.BasePermission):
    """
    Permission check: User must be authenticated, be a provider,
    and have a nurse profile.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if not request.user.can_login:
            return False
        
        if request.user.role != UserRole.PROVIDER:
            return False
        
        # Check if user has a nurse profile
        try:
            provider = request.user.provider_profile
            return hasattr(provider, 'nurse_profile') and provider.nurse_profile is not None
        except Exception:
            return False


class IsDoctor(permissions.BasePermission):
    """
    Permission check: User must be authenticated, be a provider,
    and have a doctor profile.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if not request.user.can_login:
            return False
        
        if request.user.role != UserRole.PROVIDER:
            return False
        
        # Check if user has a doctor profile
        try:
            provider = request.user.provider_profile
            return hasattr(provider, 'doctor_profile') and provider.doctor_profile is not None
        except Exception:
            return False


class IsClinic(permissions.BasePermission):
    """
    Permission check: User must be authenticated, be a provider,
    and have a clinic profile.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if not request.user.can_login:
            return False
        
        if request.user.role != UserRole.PROVIDER:
            return False
        
        # Check if user has a clinic profile
        try:
            provider = request.user.provider_profile
            return hasattr(provider, 'clinic_profile') and provider.clinic_profile is not None
        except Exception:
            return False


class IsDoctorOrClinic(permissions.BasePermission):
    """
    Permission check: User must be authenticated, be a provider,
    and have either a doctor or clinic profile.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if not request.user.can_login:
            return False
        
        if request.user.role != UserRole.PROVIDER:
            return False
        
        # Check if user has a doctor or clinic profile
        try:
            provider = request.user.provider_profile
            has_doctor = hasattr(provider, 'doctor_profile') and provider.doctor_profile is not None
            has_clinic = hasattr(provider, 'clinic_profile') and provider.clinic_profile is not None
            return has_doctor or has_clinic
        except Exception:
            return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission: User can only access their own resources,
    unless they are an admin.
    
    Use this for viewsets where providers should only see their own data.
    Handles both direct 'user' attribute and GenericForeignKey (content_object).
    """
    
    def has_object_permission(self, request, view, obj):
        # Admins can access everything
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Check if object has a user attribute (Provider, User, etc.)
        if hasattr(obj, 'user') and obj.user is not None:
            return obj.user == request.user
        
        # If object is a User, check direct match
        if isinstance(obj, User):
            return obj == request.user
        
        # Handle GenericForeignKey (for SocialMediaLink, etc.)
        if hasattr(obj, 'content_object') and obj.content_object is not None:
            content_obj = obj.content_object
            
            # Direct user match
            if isinstance(content_obj, User):
                return content_obj == request.user
            
            # Object has user attribute (Provider, Doctor, Nurse, etc.)
            if hasattr(content_obj, 'user'):
                return content_obj.user == request.user
            
            # Object is a Provider - check if it belongs to the user
            if hasattr(request.user, 'provider_profile'):
                provider = request.user.provider_profile
                
                # Content object is the provider itself
                if content_obj == provider:
                    return True
                
                # Content object is a doctor profile of this provider
                if hasattr(provider, 'doctor_profile') and content_obj == provider.doctor_profile:
                    return True
                
                # Content object is a nurse profile of this provider
                if hasattr(provider, 'nurse_profile') and content_obj == provider.nurse_profile:
                    return True
                
                # Content object is a clinic profile of this provider
                if hasattr(provider, 'clinic_profile') and content_obj == provider.clinic_profile:
                    return True
        
        return False


class IsDoctorOrClinicOrAdmin(permissions.BasePermission):
    """
    Permission check: User must be authenticated and be either:
    - A doctor (provider with doctor profile)
    - A clinic (provider with clinic profile)
    - An admin
    
    Use this for create actions where doctors, clinics, and admins can all create.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if not request.user.can_login:
            return False
        
        # Admins can do everything
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Check if provider with doctor or clinic profile
        if request.user.role != UserRole.PROVIDER:
            return False
        
        try:
            provider = request.user.provider_profile
            has_doctor = hasattr(provider, 'doctor_profile') and provider.doctor_profile is not None
            has_clinic = hasattr(provider, 'clinic_profile') and provider.clinic_profile is not None
            return has_doctor or has_clinic
        except Exception:
            return False
