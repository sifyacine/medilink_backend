"""
Views for Medical Records app.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import User
from common.enums import UserRole

from medical_record.models import (
    MedicalRecord,
    MedicalRecordAttachment,
    MedicalRecordNote,
)
from medical_record.serializers import (
    MedicalRecordListSerializer,
    MedicalRecordDetailSerializer,
    MedicalRecordCreateSerializer,
    MedicalRecordUpdateSerializer,
    MedicalRecordAttachmentSerializer,
    MedicalRecordNoteSerializer,
)
from medical_record.permissions import (
    IsPatientOwnerOrAuthorizedProvider,
    CanCreateMedicalRecord,
    CanModifyMedicalRecord,
    CanDeleteMedicalRecord,
)


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
        
        # Providers can see all patient records (if approved)
        elif self.request.user.role == UserRole.PROVIDER:
            queryset = queryset.filter(patient__role=UserRole.PATIENT)
        
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
