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
from django.utils import timezone

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
    filterset_fields = ['record_type', 'is_active', 'requires_followup', 'patient', 'patient_record']
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
            queryset = queryset.filter(
                models.Q(patient=self.request.user) |
                models.Q(patient_record__linked_user=self.request.user)
            )
        
        # Providers can see records of patients they have access to
        elif self.request.user.role == UserRole.PROVIDER:
            try:
                provider = self.request.user.provider_profile
                # Get patients this provider has access to
                authorized_patient_ids = ProviderAccess.objects.filter(
                    provider=provider,
                    is_active=True
                ).values_list('patient_id', flat=True)

                # Legacy patient-record access grants (used by appointment/nurse request workflows)
                from patients.models import ProviderPatientAccess
                authorized_patient_record_ids = ProviderPatientAccess.objects.filter(
                    provider=provider
                ).values_list('patient_record_id', flat=True)
                
                # Also include records they created
                queryset = queryset.filter(
                    models.Q(patient_id__in=authorized_patient_ids) |
                    models.Q(patient_record_id__in=authorized_patient_record_ids) |
                    models.Q(patient_record__linked_user_id__in=authorized_patient_ids) |
                    models.Q(created_by=self.request.user)
                ).distinct()
            except Exception:
                queryset = queryset.filter(created_by=self.request.user)
        
        # Admins can see all records
        # (no filtering needed)
        
        return queryset.select_related(
            'patient',
            'patient_record',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'prescription',
            'allergy',
            'attachments',
            'notes'
        )
    
    def perform_create(self, serializer):
        """Create medical record."""
        serializer.save()
    
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
        
        queryset = self.get_queryset()
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
        
        queryset = self.get_queryset().filter(
            models.Q(patient=patient) |
            models.Q(patient_record__linked_user=patient)
        )
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='my-health-data')
    def my_health_data(self, request):
        """
        Return a consolidated health-data bundle for the authenticated patient.

        Includes medical records, prescriptions, appointments, nurse requests,
        and provider access grants so patients can verify full history.
        Also includes organized records by timeline, diagnosis, and severity.
        """
        if request.user.role != UserRole.PATIENT:
            return Response(
                {'error': 'This endpoint is only available for patients.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = request.user
        records_qs = self.get_queryset().filter(is_active=True).order_by('-record_date', '-created_at')

        from prescriptions.models import Prescription as RxPrescription
        prescriptions_qs = RxPrescription.objects.filter(
            models.Q(patient=user) |
            models.Q(patient_record__linked_user=user)
        ).select_related('doctor', 'clinic', 'appointment').prefetch_related('items').order_by('-created_at')

        from appointments.models import Appointment
        appointments_qs = Appointment.objects.filter(
            models.Q(patient_user=user) |
            models.Q(patient_record__linked_user=user)
        ).select_related('provider').order_by('-appointment_date', '-created_at')

        from nurse_requests.models import NurseServiceRequest
        nurse_requests_qs = NurseServiceRequest.objects.filter(
            models.Q(patient_user=user) |
            models.Q(patient_record__linked_user=user)
        ).select_related('service', 'accepted_nurse').order_by('-created_at')

        from medical_record.models import ProviderAccess
        provider_access_qs = ProviderAccess.objects.filter(patient=user).select_related('provider__user').order_by('-granted_at')

        from patients.models import ProviderPatientAccess
        legacy_access_qs = ProviderPatientAccess.objects.filter(
            patient_record__linked_user=user
        ).select_related('provider__user', 'patient_record').order_by('-created_at')

        # Organize records
        records_data = [
            {
                'id': r.id,
                'title': r.title,
                'record_type': r.record_type,
                'record_date': r.record_date,
                'description': r.description,
                'diagnosis_code': r.diagnosis_code,
                'symptoms': r.symptoms,
                'is_confidential': r.is_confidential,
                'requires_followup': r.requires_followup,
                'followup_date': r.followup_date,
                'created_at': r.created_at,
                'updated_at': r.updated_at,
                'folder_name': r.folder_name,
                'severity_level': r.severity_level,
                'sequence_number': r.sequence_number,
            }
            for r in records_qs
        ]

        # GROUP BY TIMELINE (recent first)
        timeline_records = sorted(records_data, key=lambda x: x['record_date'], reverse=True)

        # GROUP BY DIAGNOSIS
        by_diagnosis = {}
        for record in records_data:
            key = record['diagnosis_code'] or record['record_type']
            if key not in by_diagnosis:
                by_diagnosis[key] = {'diagnosis': key, 'count': 0, 'records': [], 'most_recent': None}
            by_diagnosis[key]['count'] += 1
            by_diagnosis[key]['records'].append(record)
            if by_diagnosis[key]['most_recent'] is None or record['record_date'] > by_diagnosis[key]['most_recent']['record_date']:
                by_diagnosis[key]['most_recent'] = record

        # GROUP BY SEVERITY
        by_severity = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': [],
            'INFO': [],
        }
        for record in records_data:
            severity = record.get('severity_level', 'MEDIUM')
            by_severity[severity].append(record)

        # GROUP BY FOLDER
        by_folder = {}
        for record in records_data:
            folder = record.get('folder_name') or 'Uncategorized'
            if folder not in by_folder:
                by_folder[folder] = []
            by_folder[folder].append(record)

        # RECENT RECORDS (30 days)
        from datetime import timedelta
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_records = [r for r in records_data if r['record_date'] >= thirty_days_ago]

        # CRITICAL/HIGH PRIORITY
        critical_records = [r for r in records_data if r['severity_level'] in ['CRITICAL', 'HIGH']]

        prescriptions_data = [
            {
                'id': str(p.id),
                'reference_number': p.reference_number,
                'status': p.status,
                'valid_until': p.valid_until,
                'issued_at': p.issued_at,
                'created_at': p.created_at,
                'doctor_name': p.doctor.full_name if p.doctor else None,
                'clinic_name': p.clinic.name if p.clinic else None,
                'items': [
                    {
                        'id': str(item.id),
                        'medication_name': item.medication_name,
                        'dosage': item.dosage,
                        'frequency': item.frequency,
                        'duration_days': item.duration_days,
                        'duration_text': item.duration_text,
                        'instructions': item.instructions,
                    }
                    for item in p.items.all()
                ],
            }
            for p in prescriptions_qs
        ]

        appointments_data = [
            {
                'id': str(a.id),
                'status': a.status,
                'appointment_date': a.appointment_date,
                'appointment_time': a.appointment_time,
                'created_at': a.created_at,
            }
            for a in appointments_qs
        ]

        nurse_requests_data = [
            {
                'id': r.id,
                'status': r.status,
                'service_title': r.service.title if r.service else None,
                'city': r.city,
                'final_price': r.final_price,
                'created_at': r.created_at,
                'completed_at': r.completed_at,
            }
            for r in nurse_requests_qs
        ]

        provider_access_data = [
            {
                'id': a.id,
                'provider_id': str(a.provider.id),
                'provider_email': a.provider.user.email if a.provider and a.provider.user else None,
                'access_type': a.access_type,
                'is_active': a.is_active,
                'expires_at': a.expires_at,
                'granted_at': a.granted_at,
                'source': 'medical_record.ProviderAccess',
            }
            for a in provider_access_qs
        ] + [
            {
                'id': a.id,
                'provider_id': str(a.provider.id),
                'provider_email': a.provider.user.email if a.provider and a.provider.user else None,
                'access_type': a.access_level,
                'is_active': True,
                'expires_at': None,
                'granted_at': a.created_at,
                'source': 'patients.ProviderPatientAccess',
            }
            for a in legacy_access_qs
        ]

        return Response({
            'generated_at': timezone.now(),
            'patient': {
                'id': str(user.id),
                'email': user.email,
            },
            'summary': {
                'medical_records': len(records_data),
                'critical_or_high_priority': len(critical_records),
                'recent_30_days': len(recent_records),
                'prescriptions': len(prescriptions_data),
                'appointments': len(appointments_data),
                'nurse_requests': len(nurse_requests_data),
                'provider_access_grants': len(provider_access_data),
            },
            'medical_records': {
                'all': records_data,
                'by_timeline': timeline_records,
                'by_diagnosis': list(by_diagnosis.values()),
                'by_severity': by_severity,
                'by_folder': by_folder,
                'recent_30_days': recent_records,
                'critical_or_high_priority': critical_records,
            },
            'prescriptions': prescriptions_data,
            'appointments': appointments_data,
            'nurse_requests': nurse_requests_data,
            'provider_access': provider_access_data,
        })

    
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
                models.Q(patient=request.user) |
                models.Q(patient_record__linked_user=request.user),
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
