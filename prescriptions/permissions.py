"""
Prescription permissions for the Medilink platform.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsDoctorUser(BasePermission):
    """
    Only allow doctors to access.
    """
    message = "Only doctors can perform this action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'doctor_profile')


class IsPrescriptionDoctor(BasePermission):
    """
    Only allow the doctor who created the prescription to modify it.
    """
    message = "You can only modify prescriptions you created."
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        if hasattr(request.user, 'doctor_profile'):
            return obj.doctor == request.user.doctor_profile
        
        return False


class CanViewPrescription(BasePermission):
    """
    Allow viewing prescription if user is:
    - The doctor who created it
    - The patient (with account)
    - Admin
    """
    message = "You do not have permission to view this prescription."
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        # Admin can view all
        if user.is_staff or user.is_superuser:
            return True
        
        # Doctor who created it
        if hasattr(user, 'doctor_profile') and obj.doctor == user.doctor_profile:
            return True
        
        # Patient with account
        if obj.patient == user:
            return True
        
        return False


class CanModifyPrescription(BasePermission):
    """
    Only allow the doctor who created the prescription to modify it,
    and only if it's in DRAFT status.
    """
    message = "You can only modify draft prescriptions you created."
    
    def has_object_permission(self, request, view, obj):
        from .models import PrescriptionStatus
        
        if request.method in SAFE_METHODS:
            return True
        
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        # Admin can modify all
        if user.is_staff or user.is_superuser:
            return True
        
        # Doctor who created it, only in draft status
        if hasattr(user, 'doctor_profile'):
            if obj.doctor == user.doctor_profile:
                return obj.status == PrescriptionStatus.DRAFT
        
        return False
