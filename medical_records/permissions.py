"""
Medical Records permissions.
"""
from rest_framework import permissions

from django.utils import timezone

from accounts.models import User
from common.enums import UserRole
from medical_records.models import MedicalRecord, ProviderAccess


class CanAccessMedicalRecord(permissions.BasePermission):
    """
    Permission check: User can access medical record if:
    1. User is the patient (owner)
    2. User is an admin
    3. User is a provider with authorized access to this patient's records
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admins can access everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Patients can access their own records
        if user.role == UserRole.PATIENT:
            return obj.patient == user
        
        # Providers need explicit authorization
        if user.role == UserRole.PROVIDER:
            try:
                provider = user.provider_profile
                # Check if provider has access to this patient
                access = ProviderAccess.objects.filter(
                    patient=obj.patient,
                    provider=provider,
                    is_active=True
                ).first()
                
                if access:
                    # Check if access has expired
                    if access.expires_at and access.expires_at < timezone.now():
                        return False
                    return True
                
                return False
            except Exception:
                return False
        
        return False


class CanCreateMedicalRecord(permissions.BasePermission):
    """
    Permission check: User can create medical record if:
    1. User is a patient (for their own records)
    2. User is an admin
    3. User is an authorized provider (for patient records)
    """
    
    def has_permission(self, request, view):
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        # Admins can create records
        if user.role == UserRole.ADMIN:
            return True
        
        # Patients can create their own records
        if user.role == UserRole.PATIENT:
            return True
        
        # Providers can create records if they have access
        if user.role == UserRole.PROVIDER:
            # Check if provider is creating record for a patient they have access to
            patient_id = request.data.get('patient')
            if patient_id:
                try:
                    from accounts.models import User
                    patient = User.objects.get(id=patient_id, role=UserRole.PATIENT)
                    provider = user.provider_profile
                    
                    access = ProviderAccess.objects.filter(
                        patient=patient,
                        provider=provider,
                        is_active=True
                    ).exists()
                    
                    return access
                except Exception:
                    return False
            
            return True  # Provider can create records (will be validated in serializer)
        
        return False


class CanManageProviderAccess(permissions.BasePermission):
    """
    Permission check: User can manage provider access if:
    1. User is the patient (can grant/revoke access to their records)
    2. User is an admin
    """
    
    def has_permission(self, request, view):
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        # Admins can manage all access
        if user.role == UserRole.ADMIN:
            return True
        
        # Patients can manage access to their own records
        if user.role == UserRole.PATIENT:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admins can manage all access
        if user.role == UserRole.ADMIN:
            return True
        
        # Patients can only manage access to their own records
        if user.role == UserRole.PATIENT:
            return obj.patient == user
        
        return False
