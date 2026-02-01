"""Permissions for the reviews app."""
from rest_framework import permissions


class IsReviewerOrReadOnly(permissions.BasePermission):
    """
    Allow read access to anyone.
    Only the reviewer can modify their own review.
    """
    
    def has_permission(self, request, view):
        # Allow read access to all
        if request.method in permissions.SAFE_METHODS:
            return True
        # Require authentication for write operations
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Allow read access to all
        if request.method in permissions.SAFE_METHODS:
            return True
        # Only the reviewer can modify
        return obj.reviewer == request.user


class CanRespondToReview(permissions.BasePermission):
    """
    Permission to respond to a review.
    Only the owner of the reviewed entity can respond.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        # Admin can always respond
        if user.is_staff or user.is_superuser:
            return True
        
        # Get the reviewed object
        reviewed_obj = obj.reviewed_object
        if not reviewed_obj:
            return False
        
        # Check if user owns the reviewed entity
        # This needs to be customized based on your models
        if hasattr(reviewed_obj, 'user'):
            return reviewed_obj.user == user
        if hasattr(reviewed_obj, 'provider'):
            return reviewed_obj.provider.user == user
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read access to anyone.
    Only admins can modify.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and (request.user.is_staff or request.user.is_superuser)
