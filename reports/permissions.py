"""Permissions for the reports app."""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Only admin users can access."""
    
    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)


class IsReporterOrAdmin(permissions.BasePermission):
    """
    Allow access to the reporter or admin users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin can always access
        if request.user.is_staff or request.user.is_superuser:
            return True
        # Reporter can view their own reports
        if request.method in permissions.SAFE_METHODS:
            return obj.reporter == request.user
        return False


class CanCreateReport(permissions.BasePermission):
    """Any authenticated user can create a report."""
    
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user and request.user.is_authenticated
        return True
