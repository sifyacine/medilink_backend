"""
Views for Medical Records app.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db import models

from accounts.models import User
from common.enums import UserRole

from medical_record.models import (
    MedicalRecord,
    MedicalRecordAttachment,
    MedicalRecordNote,
    ProviderAccess,
    MedicalRecordAccessLog,
)
from medical_record.serializers import (
    MedicalRecordListSerializer,
    MedicalRecordDetailSerializer,
    MedicalRecordCreateSerializer,
    MedicalRecordUpdateSerializer,
    MedicalRecordAttachmentSerializer,
    MedicalRecordNoteSerializer,
    ProviderAccessSerializer,
    ProviderAccessCreateSerializer,
)
from medical_record.permissions import (
    IsPatientOwnerOrAuthorizedProvider,
    CanCreateMedicalRecord,
    CanModifyMedicalRecord,
    CanDeleteMedicalRecord,
    CanManageProviderAccess,
    has_provider_access,
)
from medical_record.services import MedicalRecordPDFService


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for medical records.
    
    Provides CRUD operations with proper permission enforcement.
    """
    queryset = MedicalRecord.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsPatientOwnerOrAuthorizedProvider,
        CanCreateMedicalRecord,
        CanModifyMedicalRecord,
    ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['record_type', 'is_active', 'requires_followup', 'patient']
    search_fields = ['title', 'description', 'symptoms', 'diagnosis_code']
    ordering_fields = ['record_date', 'created_at', 'updated_at']
    ordering = ['-record_date', '-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return MedicalRecordListSerializer
        elif self.action == 'create':
            return MedicalRecordCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MedicalRecordUpdateSerializer
        return MedicalRecordDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        queryset = super().get_queryset()
        
        # Patients can only see their own records
        if self.request.user.role == UserRole.PATIENT:
            queryset = queryset.filter(patient=self.request.user)
        
        # Providers can see records of patients they have access to
        elif self.request.user.role == UserRole.PROVIDER:
            try:
                provider = self.request.user.provider_profile
                # Get patients this provider has access to
                authorized_patient_ids = ProviderAccess.objects.filter(
                    provider=provider,
                    is_active=True
                ).values_list('patient_id', flat=True)
                
                # Also include records they created
                queryset = queryset.filter(
                    models.Q(patient_id__in=authorized_patient_ids) |
                    models.Q(created_by=self.request.user)
                ).distinct()
            except Exception:
                queryset = queryset.filter(created_by=self.request.user)
        
        # Admins can see all records
        # (no filtering needed)
        
        return queryset.select_related(
            'patient',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'prescription',
            'allergy',
            'attachments',
            'notes'
        )
    
    def perform_create(self, serializer):
        """Create medical record and log access."""
        medical_record = serializer.save()
        
        # Log access
        from medical_record.models import MedicalRecordAccessLog
        MedicalRecordAccessLog.objects.create(
            medical_record=medical_record,
            accessed_by=self.request.user,
            access_type='CREATE',
            ip_address=self._get_client_ip()
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve medical record and log access."""
        instance = self.get_object()
        
        # Log access
        from medical_record.models import MedicalRecordAccessLog
        MedicalRecordAccessLog.objects.create(
            medical_record=instance,
            accessed_by=request.user,
            access_type='VIEW',
            ip_address=self._get_client_ip()
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete medical record (set is_active=False)."""
        instance = self.get_object()
        
        # Check delete permission
        from medical_record.permissions import CanDeleteMedicalRecord
        permission = CanDeleteMedicalRecord()
        if not permission.has_object_permission(request, self, instance):
            return Response(
                {'error': 'You do not have permission to delete this record.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete
        instance.is_active = False
        instance.save()
        
        # Log access
        from medical_record.models import MedicalRecordAccessLog
        MedicalRecordAccessLog.objects.create(
            medical_record=instance,
            accessed_by=request.user,
            access_type='DELETE',
            ip_address=self._get_client_ip()
        )
        
        return Response(
            {'message': 'Medical record has been deactivated.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='attachments')
    def add_attachment(self, request, pk=None):
        """Add attachment to medical record."""
        medical_record = self.get_object()
        
        serializer = MedicalRecordAttachmentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(
                medical_record=medical_record,
                uploaded_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='notes')
    def add_note(self, request, pk=None):
        """Add note to medical record."""
        medical_record = self.get_object()
        
        serializer = MedicalRecordNoteSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            note = serializer.save(
                medical_record=medical_record,
                created_by=request.user
            )
            
            # Lock provider notes automatically
            if request.user.role == UserRole.PROVIDER:
                note.note_type = 'PROVIDER'
                note.is_locked = True
                note.save()
            
            return Response(
                MedicalRecordNoteSerializer(note).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my-records')
    def my_records(self, request):
        """Get current user's medical records (for patients)."""
        if request.user.role != UserRole.PATIENT:
            return Response(
                {'error': 'This endpoint is only available for patients.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(patient=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>[^/.]+)')
    def patient_records(self, request, patient_id=None):
        """Get medical records for a specific patient (for providers/admins)."""
        if request.user.role == UserRole.PATIENT:
            return Response(
                {'error': 'Patients can only access their own records.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient = User.objects.get(id=patient_id, role=UserRole.PATIENT)
        except User.DoesNotExist:
            return Response(
                {'error': 'Patient not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = self.get_queryset().filter(patient=patient)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def _get_client_ip(self):
        """Get client IP address from request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')
    
    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """
        Export a single medical record as PDF.
        
        GET /api/medical-records/{id}/export-pdf/
        
        Query params:
            include_attachments: bool - Include attachment list (default: false)
        """
        medical_record = self.get_object()
        
        # Check if PDF service is available
        if not MedicalRecordPDFService.is_available():
            return Response(
                {'error': 'PDF generation is not available. Install reportlab package.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        include_attachments = request.query_params.get('include_attachments', 'false').lower() == 'true'
        
        try:
            # Generate PDF
            pdf_buffer = MedicalRecordPDFService.generate_single_record_pdf(
                medical_record,
                include_attachments=include_attachments
            )
            
            # Log access
            MedicalRecordAccessLog.objects.create(
                medical_record=medical_record,
                accessed_by=request.user,
                access_type='PDF_EXPORT',
                ip_address=self._get_client_ip()
            )
            
            # Return PDF response
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            filename = f"medical_record_{medical_record.id}_{medical_record.record_date}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='export-summary')
    def export_summary(self, request):
        """
        Export all medical records as a summary PDF.
        Only for patients to export their own records.
        
        GET /api/medical-records/export-summary/
        """
        if request.user.role != UserRole.PATIENT:
            return Response(
                {'error': 'Only patients can export their own medical record summary.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not MedicalRecordPDFService.is_available():
            return Response(
                {'error': 'PDF generation is not available. Install reportlab package.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            # Get patient's records
            records = MedicalRecord.objects.filter(
                patient=request.user,
                is_active=True
            ).select_related('created_by').prefetch_related(
                'prescription', 'allergy'
            ).order_by('-record_date')
            
            # Generate PDF
            pdf_buffer = MedicalRecordPDFService.generate_patient_summary_pdf(
                request.user,
                records
            )
            
            # Return PDF response
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            filename = f"medical_records_summary_{request.user.id}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProviderAccessViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing provider access to patient records.
    
    Patients can grant/revoke access to their records.
    Providers can view their access grants.
    Admins can manage all access grants.
    """
    permission_classes = [IsAuthenticated, CanManageProviderAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active', 'access_type']
    ordering_fields = ['granted_at', 'expires_at']
    ordering = ['-granted_at']
    
    def get_queryset(self):
        """Return access grants based on user role."""
        user = self.request.user
        
        if user.role == UserRole.ADMIN:
            return ProviderAccess.objects.all().select_related('patient', 'provider__user')
        
        if user.role == UserRole.PATIENT:
            return ProviderAccess.objects.filter(patient=user).select_related('provider__user')
        
        if user.role == UserRole.PROVIDER:
            try:
                provider = user.provider_profile
                return ProviderAccess.objects.filter(provider=provider).select_related('patient')
            except Exception:
                return ProviderAccess.objects.none()
        
        return ProviderAccess.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProviderAccessCreateSerializer
        return ProviderAccessSerializer
    
    def perform_create(self, serializer):
        """Set access_granted_by when creating."""
        serializer.save(access_granted_by=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='my-providers')
    def my_providers(self, request):
        """
        Get list of providers who have access to patient's records.
        Only for patients.
        """
        if request.user.role != UserRole.PATIENT:
            return Response(
                {'error': 'This endpoint is only for patients.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        accesses = ProviderAccess.objects.filter(
            patient=request.user,
            is_active=True
        ).select_related('provider__user')
        
        serializer = ProviderAccessSerializer(accesses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-patients')
    def my_patients(self, request):
        """
        Get list of patients the provider has access to.
        Only for providers.
        """
        if request.user.role != UserRole.PROVIDER:
            return Response(
                {'error': 'This endpoint is only for providers.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            provider = request.user.provider_profile
            accesses = ProviderAccess.objects.filter(
                provider=provider,
                is_active=True
            ).select_related('patient')
            
            serializer = ProviderAccessSerializer(accesses, many=True)
            return Response(serializer.data)
        except Exception:
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], url_path='revoke')
    def revoke(self, request, pk=None):
        """Revoke provider access."""
        access = self.get_object()
        access.is_active = False
        access.save()
        
        return Response({
            'message': 'Provider access has been revoked.',
            'access': ProviderAccessSerializer(access).data
        })
    
    @action(detail=True, methods=['post'], url_path='renew')
    def renew(self, request, pk=None):
        """Renew provider access (reactivate)."""
        access = self.get_object()
        access.is_active = True
        access.expires_at = None  # Remove expiration
        access.save()
        
        return Response({
            'message': 'Provider access has been renewed.',
            'access': ProviderAccessSerializer(access).data
        })
