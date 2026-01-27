"""
Medical Records views and viewsets.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from medical_records.models import (
    MedicalRecord,
    Prescription,
    Allergy,
    MedicalRecordAttachment,
    MedicalRecordNote,
    ProviderAccess,
)
from medical_records.serializers import (
    MedicalRecordSerializer,
    PrescriptionSerializer,
    AllergySerializer,
    MedicalRecordAttachmentSerializer,
    MedicalRecordNoteSerializer,
    ProviderAccessSerializer,
)
from medical_records.permissions import (
    CanAccessMedicalRecord,
    CanCreateMedicalRecord,
    CanManageProviderAccess,
)
from accounts.models import User
from common.enums import UserRole
from django.utils import timezone


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Medical Records.
    
    GET /api/medical-records/ - List records (patient sees own, provider sees authorized)
    GET /api/medical-records/{id}/ - Get record details
    POST /api/medical-records/ - Create record
    PUT/PATCH /api/medical-records/{id}/ - Update record
    DELETE /api/medical-records/{id}/ - Delete record (soft delete)
    """
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated, CanCreateMedicalRecord]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['record_type', 'is_active', 'is_confidential']
    search_fields = ['title', 'diagnosis', 'symptoms', 'treatment']
    ordering_fields = ['record_date', 'created_at']
    ordering = ['-record_date', '-created_at']
    
    def get_queryset(self):
        """Return records based on user role and permissions."""
        user = self.request.user
        
        if user.role == UserRole.ADMIN:
            # Admins see all records
            return MedicalRecord.objects.all()
        
        elif user.role == UserRole.PATIENT:
            # Patients see only their own records
            return MedicalRecord.objects.filter(patient=user)
        
        elif user.role == UserRole.PROVIDER:
            # Providers see records for patients they have access to
            try:
                provider = user.provider_profile
                # Get list of patients this provider has access to
                authorized_patients = ProviderAccess.objects.filter(
                    provider=provider,
                    is_active=True
                ).values_list('patient_id', flat=True)
                
                return MedicalRecord.objects.filter(patient_id__in=authorized_patients)
            except Exception:
                return MedicalRecord.objects.none()
        
        return MedicalRecord.objects.none()
    
    def get_permissions(self):
        """Use object-level permission for retrieve/update/delete."""
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanAccessMedicalRecord()]
        return [IsAuthenticated(), CanCreateMedicalRecord()]
    
    def perform_create(self, serializer):
        """Set created_by when creating record."""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating record."""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_prescription(self, request, pk=None):
        """
        Add prescription to medical record.
        
        POST /api/medical-records/{id}/add_prescription/
        """
        record = self.get_object()
        serializer = PrescriptionSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(medical_record=record)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        """
        Add attachment to medical record.
        
        POST /api/medical-records/{id}/add_attachment/
        """
        record = self.get_object()
        serializer = MedicalRecordAttachmentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                medical_record=record,
                uploaded_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """
        Add note to medical record.
        
        POST /api/medical-records/{id}/add_note/
        """
        record = self.get_object()
        serializer = MedicalRecordNoteSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(
                medical_record=record,
                author=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllergyViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Allergies.
    
    GET /api/allergies/ - List allergies (patient sees own)
    POST /api/allergies/ - Create allergy
    PUT/PATCH /api/allergies/{id}/ - Update allergy
    DELETE /api/allergies/{id}/ - Delete allergy
    """
    serializer_class = AllergySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return allergies for the authenticated patient."""
        user = self.request.user
        
        if user.role == UserRole.ADMIN:
            return Allergy.objects.all()
        
        # Patients see only their own allergies
        if user.role == UserRole.PATIENT:
            return Allergy.objects.filter(patient=user)
        
        # Providers can see allergies for patients they have access to
        if user.role == UserRole.PROVIDER:
            try:
                provider = user.provider_profile
                authorized_patients = ProviderAccess.objects.filter(
                    provider=provider,
                    is_active=True
                ).values_list('patient_id', flat=True)
                
                return Allergy.objects.filter(patient_id__in=authorized_patients)
            except Exception:
                return Allergy.objects.none()
        
        return Allergy.objects.none()
    
    def perform_create(self, serializer):
        """Set patient when creating allergy."""
        user = self.request.user
        if user.role == UserRole.PATIENT:
            serializer.save(patient=user)
        else:
            # Provider or admin creating for a patient
            serializer.save()


class ProviderAccessViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Provider Access management.
    
    GET /api/provider-access/ - List access grants
    POST /api/provider-access/ - Grant access to provider
    PUT/PATCH /api/provider-access/{id}/ - Update access
    DELETE /api/provider-access/{id}/ - Revoke access
    """
    serializer_class = ProviderAccessSerializer
    permission_classes = [IsAuthenticated, CanManageProviderAccess]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['patient', 'provider', 'is_active', 'access_type']
    
    def get_queryset(self):
        """Return access grants based on user role."""
        user = self.request.user
        
        if user.role == UserRole.ADMIN:
            return ProviderAccess.objects.all()
        
        elif user.role == UserRole.PATIENT:
            # Patients see access grants for their records
            return ProviderAccess.objects.filter(patient=user)
        
        elif user.role == UserRole.PROVIDER:
            # Providers see access grants they have
            try:
                provider = user.provider_profile
                return ProviderAccess.objects.filter(provider=provider)
            except Exception:
                return ProviderAccess.objects.none()
        
        return ProviderAccess.objects.none()
    
    def perform_create(self, serializer):
        """Set access_granted_by when creating access grant."""
        serializer.save(access_granted_by=self.request.user)
