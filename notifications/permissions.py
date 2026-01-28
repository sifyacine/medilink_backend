"""
Permissions for the Notifications app.
"""
from rest_framework.permissions import BasePermission


class IsNotificationOwner(BasePermission):
    """
    Permission that only allows the notification recipient to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user


class IsDeviceTokenOwner(BasePermission):
    """
    Permission that only allows the device token owner to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CanSendBulkNotifications(BasePermission):
    """
    Permission for sending bulk notifications.
    Only staff and admins can send bulk notifications.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.is_superuser or
            getattr(request.user, 'role', None) == 'ADMIN'
        )
