"""
Invoice permissions for the Medilink platform.

Permissions:
- Providers can manage their own invoices
- Patients can view their own invoices
- Admins have full access
"""
from rest_framework import permissions

from common.enums import UserRole


class IsProviderOwner(permissions.BasePermission):
    """
    Permission that allows only the provider who owns the invoice.
    """
    message = "You can only access your own invoices."
    
    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Check if user is the provider
        if hasattr(request.user, 'provider_profile'):
            return obj.provider == request.user.provider_profile
        
        return False


class IsInvoiceParticipant(permissions.BasePermission):
    """
    Permission that allows the provider who issued the invoice
    or the patient who received it.
    """
    message = "You can only access invoices you are involved in."
    
    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Provider who issued the invoice
        if hasattr(request.user, 'provider_profile'):
            if obj.provider == request.user.provider_profile:
                return True
        
        # Patient who received the invoice
        if obj.patient_user == request.user:
            return True
        
        # Check if patient_record is linked to user
        if obj.patient_record and obj.patient_record.linked_user == request.user:
            return True
        
        return False


class CanManageInvoice(permissions.BasePermission):
    """
    Permission for managing invoices (create, update, delete).
    Only providers and admins can manage invoices.
    """
    message = "Only providers can manage invoices."
    
    def has_permission(self, request, view):
        # Admins have full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Only providers can create/manage invoices
        if request.user.role == UserRole.PROVIDER:
            return hasattr(request.user, 'provider_profile')
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Provider must own the invoice
        if hasattr(request.user, 'provider_profile'):
            return obj.provider == request.user.provider_profile
        
        return False


class CanViewInvoice(permissions.BasePermission):
    """
    Permission for viewing invoices.
    Providers can view their own invoices.
    Patients can view invoices issued to them.
    Admins can view all.
    """
    message = "You don't have permission to view this invoice."
    
    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Provider who issued the invoice
        if hasattr(request.user, 'provider_profile'):
            if obj.provider == request.user.provider_profile:
                return True
        
        # Patient who received the invoice
        if obj.patient_user == request.user:
            return True
        
        # Patient with linked record
        if obj.patient_record:
            if hasattr(request.user, 'patient_record'):
                if obj.patient_record == request.user.patient_record:
                    return True
            if obj.patient_record.linked_user == request.user:
                return True
        
        return False


class CanManagePayment(permissions.BasePermission):
    """
    Permission for managing payments.
    Only the provider who issued the invoice or admins can manage payments.
    """
    message = "Only the invoice provider can manage payments."
    
    def has_permission(self, request, view):
        # Admins have full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Only providers can manage payments
        return request.user.role == UserRole.PROVIDER
    
    def has_object_permission(self, request, view, obj):
        # obj here is a Payment
        invoice = obj.invoice
        
        # Admins have full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Provider must own the invoice
        if hasattr(request.user, 'provider_profile'):
            return invoice.provider == request.user.provider_profile
        
        return False
