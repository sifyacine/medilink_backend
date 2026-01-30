"""
Prescription permissions for the Medilink platform.

Relationship chain:
- User -> provider_profile (Provider) -> doctor_profile (Doctor)
- User is NOT directly linked to Doctor
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS
from common.enums import ProviderStatus


def get_doctor_from_user(user):
    """
    Helper function to get Doctor instance from a User.
    Returns None if user is not a doctor.
    
    Relationship: User -> provider_profile (Provider) -> doctor_profile (Doctor)
    """
    if not user or not user.is_authenticated:
        return None
    
    try:
        provider = getattr(user, 'provider_profile', None)
        if provider and provider.status == ProviderStatus.APPROVED:
            return getattr(provider, 'doctor_profile', None)
    except Exception:
        pass
    
    return None


class IsDoctorUser(BasePermission):
    """
    Only allow approved doctors to access.
    Checks User -> provider_profile -> doctor_profile chain.
    """
    message = "Only doctors can perform this action."
    
    def has_permission(self, request, view):
        doctor = get_doctor_from_user(request.user)
        return doctor is not None


class IsPrescriptionDoctor(BasePermission):
    """
    Only allow the doctor who created the prescription to modify it.
    """
    message = "You can only modify prescriptions you created."
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        
        doctor = get_doctor_from_user(request.user)
        if doctor:
            return obj.doctor == doctor
        
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
        doctor = get_doctor_from_user(user)
        if doctor and obj.doctor == doctor:
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
        doctor = get_doctor_from_user(user)
        if doctor and obj.doctor == doctor:
            return obj.status == PrescriptionStatus.DRAFT
        
        return False
