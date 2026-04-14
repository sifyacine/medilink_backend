"""
Prescription permissions for the Medilink platform.

Relationship chain:
- User -> provider_profile (Provider) -> doctor_profile (Doctor)
- User is NOT directly linked to Doctor
"""

import contextlib
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

    with contextlib.suppress(Exception):
        provider = getattr(user, 'provider_profile', None)
        if provider and provider.status == ProviderStatus.APPROVED:
            return getattr(provider, 'doctor_profile', None)
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
        if request.user.is_staff or request.user.is_superuser:
            return True

        doctor = get_doctor_from_user(request.user)
        return obj.doctor == doctor if doctor else False


class CanViewPrescription(BasePermission):
    """
    Allow viewing prescription if user is:
    - The doctor who created it
    - The patient (direct or linked)
    - Admin
    - A provider with granted access to the patient/record
    """
    message = "You do not have permission to view this prescription."
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        # Admin can view all
        if user.is_staff or user.is_superuser:
            return True
        
        # Patient check (direct or linked)
        if obj.patient == user or (obj.patient_record and obj.patient_record.linked_user == user):
            return True
            
        # Provider check
        from common.enums import UserRole
        if user.role == UserRole.PROVIDER:
            provider = getattr(user, 'provider_profile', None)
            if not provider:
                return False
                
            # Is creator?
            doctor = getattr(provider, 'doctor_profile', None)
            if doctor and obj.doctor == doctor:
                return True
                
            # Has granted access?
            if obj.patient:
                from medical_record.models import ProviderAccess
                if ProviderAccess.objects.filter(patient=obj.patient, provider=provider, is_active=True).exists():
                    return True
            if obj.patient_record:
                from patients.models import ProviderPatientAccess
                if ProviderPatientAccess.objects.filter(patient_record=obj.patient_record, provider=provider).exists():
                    return True
        
        return False


class CanModifyPrescription(BasePermission):
    """
    Only allow the doctor who created the prescription to modify it,
    and only if it's in DRAFT status.
    Admins can modify all.
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
