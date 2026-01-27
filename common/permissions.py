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


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission: User can only access their own resources,
    unless they are an admin.
    
    Use this for viewsets where providers should only see their own data.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admins can access everything
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Check if object has a user attribute (Provider, User, etc.)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # If object is a User, check direct match
        if isinstance(obj, User):
            return obj == request.user
        
        return False
