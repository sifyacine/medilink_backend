"""
Views for Medical Records app.
"""
from datetime import timedelta

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.http import HttpResponse
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
    MedicalRecordAccessLogSerializer,
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


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def _valid_access_q():
    """Return a Q that filters ProviderAccess to non-expired active grants."""
    now = timezone.now()
    return models.Q(is_active=True) & (
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
    )


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for medical records with role-based filtering.

    Patients: own records only.
    Approved providers: records of patients they have a valid (non-expired) ProviderAccess grant for,
                        plus records they created themselves.
    Admins: all records.

    Confidentiality: providers with LIMITED access cannot see records marked is_confidential=True.
    """
    permission_classes = [IsAuthenticated, IsPatientOwnerOrAuthorizedProvider, CanCreateMedicalRecord, CanModifyMedicalRecord]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['record_type', 'is_active', 'requires_followup', 'severity_level', 'folder_name']
    search_fields = ['title', 'description', 'symptoms', 'diagnosis_code']
    ordering_fields = ['record_date', 'created_at', 'updated_at', 'severity_level']
    ordering = ['-record_date', '-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return MedicalRecordListSerializer
        if self.action == 'create':
            return MedicalRecordCreateSerializer
        if self.action in ['update', 'partial_update']:
            return MedicalRecordUpdateSerializer
        return MedicalRecordDetailSerializer

    def get_queryset(self):
        user = self.request.user
        base_qs = MedicalRecord.objects.select_related(
            'patient', 'patient_record', 'created_by', 'updated_by',
        ).prefetch_related('prescription', 'allergy', 'attachments', 'notes')

        if user.role == UserRole.PATIENT:
            return base_qs.filter(
                models.Q(patient=user) |
                models.Q(patient_record__linked_user=user)
            )

        if user.role == UserRole.PROVIDER:
            try:
                provider = user.provider_profile
            except Exception:
                return base_qs.none()

            now = timezone.now()
            valid_access = _valid_access_q()

            # Patient IDs the provider has any valid access to
            authorized_patient_ids = ProviderAccess.objects.filter(
                valid_access, provider=provider,
            ).values_list('patient_id', flat=True)

            # Patient IDs with LIMITED access (confidential records excluded)
            limited_patient_ids = ProviderAccess.objects.filter(
                valid_access, provider=provider, access_type='LIMITED',
            ).values_list('patient_id', flat=True)

            # Legacy ProviderPatientAccess (no expiry)
            from patients.models import ProviderPatientAccess
            authorized_pr_ids = ProviderPatientAccess.objects.filter(
                provider=provider
            ).values_list('patient_record_id', flat=True)

            qs = base_qs.filter(
                models.Q(patient_id__in=authorized_patient_ids) |
                models.Q(patient_record_id__in=authorized_pr_ids) |
                models.Q(patient_record__linked_user_id__in=authorized_patient_ids) |
                models.Q(created_by=user)
            ).distinct()

            # Exclude confidential records for LIMITED access patients
            qs = qs.exclude(
                models.Q(patient_id__in=limited_patient_ids, is_confidential=True) |
                models.Q(patient_record__linked_user_id__in=limited_patient_ids, is_confidential=True)
            )

            return qs

        # Admins see everything
        return base_qs

    def perform_create(self, serializer):
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        MedicalRecordAccessLog.objects.create(
            medical_record=instance,
            accessed_by=request.user,
            access_type='VIEW',
            ip_address=_get_client_ip(request),
        )
        return Response(self.get_serializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        perm = CanDeleteMedicalRecord()
        if not perm.has_object_permission(request, self, instance):
            return Response(
                {'error': 'You do not have permission to delete this record.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        MedicalRecordAccessLog.objects.create(
            medical_record=instance,
            accessed_by=request.user,
            access_type='DELETE',
            ip_address=_get_client_ip(request),
        )
        return Response({'message': 'Medical record deactivated.'}, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Attachment & note sub-actions
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post', 'get'], url_path='attachments')
    def attachments(self, request, pk=None):
        """GET list / POST upload attachment on a medical record."""
        record = self.get_object()
        if request.method == 'GET':
            return Response(
                MedicalRecordAttachmentSerializer(
                    record.attachments.all(), many=True, context={'request': request}
                ).data
            )
        serializer = MedicalRecordAttachmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(medical_record=record, uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'get'], url_path='notes')
    def notes(self, request, pk=None):
        """GET list / POST add note on a medical record."""
        record = self.get_object()
        if request.method == 'GET':
            return Response(
                MedicalRecordNoteSerializer(
                    record.notes.all(), many=True, context={'request': request}
                ).data
            )
        serializer = MedicalRecordNoteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            note = serializer.save(medical_record=record, created_by=request.user)
            if request.user.role == UserRole.PROVIDER:
                note.note_type = 'PROVIDER'
                note.is_locked = True
                note.save(update_fields=['note_type', 'is_locked'])
            return Response(MedicalRecordNoteSerializer(note).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='access-logs')
    def access_logs(self, request, pk=None):
        """
        Return the access audit trail for a single record.
        Only the owning patient or admins may view this.

        GET /api/medical-records/records/{id}/access-logs/
        """
        record = self.get_object()
        if request.user.role not in (UserRole.PATIENT, UserRole.ADMIN):
            return Response(
                {'error': 'Only patients and admins can view access logs.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        logs = record.access_logs.select_related('accessed_by').order_by('-accessed_at')
        return Response(MedicalRecordAccessLogSerializer(logs, many=True).data)

    # ------------------------------------------------------------------
    # Patient-scoped views
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='my-folder')
    def my_folder(self, request):
        """
        Patient's own structured medical folder — mirrors the provider-facing
        `patient-folder` view but scoped to the authenticated patient.

        Returns patient demographics, records grouped by type/folder/severity,
        active allergies, pending follow-ups, and recent activity.

        GET /api/medical-records/records/my-folder/
        """
        if request.user.role != UserRole.PATIENT:
            return Response(
                {'error': 'This endpoint is only for patients.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = request.user
        records_qs = self.get_queryset().filter(
            is_active=True,
        ).order_by('-record_date', '-created_at')

        records_data = MedicalRecordDetailSerializer(records_qs, many=True, context={'request': request}).data

        # Patient demographics from linked PatientRecord if available
        patient_info = {'id': str(user.id), 'email': user.email}
        try:
            pr = user.patient_record
            patient_info.update({
                'full_name': pr.full_name,
                'date_of_birth': pr.date_of_birth,
                'age': pr.age,
                'gender': pr.gender,
                'blood_type': pr.blood_type,
                'known_allergies': pr.known_allergies,
                'chronic_conditions': pr.chronic_conditions,
                'current_medications': pr.current_medications,
                'emergency_contact_name': pr.emergency_contact_name,
                'emergency_contact_phone': pr.emergency_contact_phone,
                'patient_unique_id': pr.patient_unique_id,
            })
        except Exception:
            pass

        by_type = {}
        by_folder = {}
        active_allergies = []
        pending_followups = []
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_records = []

        for r in records_data:
            rt = r.get('record_type')
            by_type.setdefault(rt, []).append(r)

            folder = r.get('folder_name') or 'General'
            by_folder.setdefault(folder, []).append(r)

            if rt == 'ALLERGY' and r.get('allergy'):
                active_allergies.append(r)

            if r.get('requires_followup') and r.get('followup_date'):
                pending_followups.append(r)

            if r.get('record_date') and r['record_date'] >= str(thirty_days_ago):
                recent_records.append(r)

        critical_records = [r for r in records_data if r.get('severity_level') in ('CRITICAL', 'HIGH')]

        return Response({
            'generated_at': timezone.now(),
            'patient': patient_info,
            'summary': {
                'total_records': len(records_data),
                'active_allergies': len(active_allergies),
                'pending_followups': len(pending_followups),
                'critical_or_high': len(critical_records),
                'recent_30_days': len(recent_records),
                'record_types': {k: len(v) for k, v in by_type.items()},
            },
            'medical_records': {
                'timeline': records_data,
                'by_type': by_type,
                'by_folder': by_folder,
                'critical_or_high': critical_records,
                'recent_30_days': recent_records,
                'pending_followups': pending_followups,
            },
            'active_allergies': active_allergies,
        })

    @action(detail=False, methods=['get'], url_path='my-records')
    def my_records(self, request):
        """Patient's own records, paginated."""
        if request.user.role != UserRole.PATIENT:
            return Response(
                {'error': 'This endpoint is only for patients.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        qs = self.get_queryset().filter(is_active=True)
        page = self.paginate_queryset(qs)
        serializer = MedicalRecordListSerializer(page or qs, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='my-health-data')
    def my_health_data(self, request):
        """
        Consolidated health-data bundle for the authenticated patient.
        Includes medical records (grouped), prescriptions, appointments,
        nurse requests, and provider access grants.
        """
        if request.user.role != UserRole.PATIENT:
            return Response(
                {'error': 'This endpoint is only for patients.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = request.user
        records_qs = self.get_queryset().filter(is_active=True).order_by('-record_date', '-created_at')

        from prescriptions.models import Prescription as RxPrescription
        prescriptions_qs = RxPrescription.objects.filter(
            models.Q(patient=user) | models.Q(patient_record__linked_user=user)
        ).select_related('doctor', 'clinic', 'appointment').prefetch_related('items').order_by('-created_at')

        from appointments.models import Appointment
        appointments_qs = Appointment.objects.filter(
            models.Q(patient_user=user) | models.Q(patient_record__linked_user=user)
        ).select_related('provider').order_by('-appointment_date', '-created_at')

        from nurse_requests.models import NurseServiceRequest
        nurse_requests_qs = NurseServiceRequest.objects.filter(
            models.Q(patient_user=user) | models.Q(patient_record__linked_user=user)
        ).select_related('service', 'accepted_nurse').order_by('-created_at')

        provider_access_qs = ProviderAccess.objects.filter(patient=user).select_related('provider__user').order_by('-granted_at')

        from patients.models import ProviderPatientAccess
        legacy_access_qs = ProviderPatientAccess.objects.filter(
            patient_record__linked_user=user
        ).select_related('provider__user', 'patient_record').order_by('-created_at')

        records_data = MedicalRecordListSerializer(records_qs, many=True, context={'request': request}).data

        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent = [r for r in records_data if r['record_date'] and r['record_date'] >= str(thirty_days_ago)]
        critical = [r for r in records_data if r.get('severity_level') in ('CRITICAL', 'HIGH')]
        pending_followups = [r for r in records_data if r.get('requires_followup') and r.get('followup_date')]

        by_type = {}
        by_folder = {}
        for r in records_data:
            rt = r['record_type']
            by_type.setdefault(rt, []).append(r)
            folder = r.get('folder_name') or 'Uncategorized'
            by_folder.setdefault(folder, []).append(r)

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

        provider_access_data = ProviderAccessSerializer(provider_access_qs, many=True).data

        return Response({
            'generated_at': timezone.now(),
            'patient': {'id': str(user.id), 'email': user.email},
            'summary': {
                'total_records': len(records_data),
                'critical_or_high': len(critical),
                'recent_30_days': len(recent),
                'pending_followups': len(pending_followups),
                'prescriptions': len(prescriptions_data),
                'appointments': len(appointments_data),
                'nurse_requests': len(nurse_requests_data),
                'provider_access_grants': len(provider_access_data),
            },
            'medical_records': {
                'timeline': records_data,
                'by_type': by_type,
                'by_folder': by_folder,
                'recent_30_days': recent,
                'critical_or_high_priority': critical,
                'pending_followups': pending_followups,
            },
            'prescriptions': prescriptions_data,
            'appointments': appointments_data,
            'nurse_requests': nurse_requests_data,
            'provider_access': provider_access_data,
        })

    # ------------------------------------------------------------------
    # Provider-scoped views
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path=r'patient/(?P<patient_id>[^/.]+)')
    def patient_records(self, request, patient_id=None):
        """
        Paginated list of medical records for a specific patient.
        For providers and admins only. Providers must have a valid access grant.
        """
        if request.user.role == UserRole.PATIENT:
            return Response(
                {'error': 'Patients can only access their own records.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            patient = User.objects.get(id=patient_id, role=UserRole.PATIENT)
        except User.DoesNotExist:
            return Response({'error': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Verify the provider actually has access before returning records
        if request.user.role == UserRole.PROVIDER:
            try:
                provider = request.user.provider_profile
            except Exception:
                return Response({'error': 'Provider profile not found.'}, status=status.HTTP_403_FORBIDDEN)
            if not has_provider_access(provider, patient=patient):
                return Response(
                    {'error': 'You do not have access to this patient\'s records.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        qs = self.get_queryset().filter(
            models.Q(patient=patient) |
            models.Q(patient_record__linked_user=patient)
        )
        page = self.paginate_queryset(qs)
        serializer = MedicalRecordListSerializer(page or qs, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=False, methods=['get'], url_path=r'patient-folder/(?P<patient_id>[^/.]+)')
    def patient_folder(self, request, patient_id=None):
        """
        Full structured medical folder for a specific patient.
        For approved providers with a valid access grant, and admins.

        Returns:
        - Patient demographics (from PatientRecord if available)
        - Records grouped by type, folder, and severity
        - Active allergies and current prescriptions highlighted
        - Pending follow-ups
        - Recent activity (last 30 days)

        GET /api/medical-records/records/patient-folder/{patient_id}/
        """
        if request.user.role == UserRole.PATIENT:
            return Response(
                {'error': 'Use /my-health-data for your own health folder.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            patient = User.objects.get(id=patient_id, role=UserRole.PATIENT)
        except User.DoesNotExist:
            return Response({'error': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

        access_type = None
        if request.user.role == UserRole.PROVIDER:
            try:
                provider = request.user.provider_profile
            except Exception:
                return Response({'error': 'Provider profile not found.'}, status=status.HTTP_403_FORBIDDEN)

            access_grant = ProviderAccess.objects.filter(
                _valid_access_q(), provider=provider, patient=patient,
            ).first()

            if not access_grant:
                # Also accept legacy ProviderPatientAccess
                from patients.models import ProviderPatientAccess
                try:
                    pr = patient.patient_record
                    ProviderPatientAccess.objects.get(provider=provider, patient_record=pr)
                    access_type = 'READ_ONLY'
                except Exception:
                    return Response(
                        {'error': 'You do not have access to this patient\'s medical folder.'},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                access_type = access_grant.access_type

        # Fetch all active records the requesting user can see (respects confidential filtering)
        records_qs = self.get_queryset().filter(
            models.Q(patient=patient) | models.Q(patient_record__linked_user=patient),
            is_active=True,
        ).order_by('-record_date', '-created_at')

        records_data = MedicalRecordDetailSerializer(records_qs, many=True, context={'request': request}).data

        # Patient demographics from linked PatientRecord if it exists
        patient_info = {'id': str(patient.id), 'email': patient.email}
        try:
            pr = patient.patient_record
            patient_info.update({
                'full_name': pr.full_name,
                'date_of_birth': pr.date_of_birth,
                'age': pr.age,
                'gender': pr.gender,
                'blood_type': pr.blood_type,
                'known_allergies': pr.known_allergies,
                'chronic_conditions': pr.chronic_conditions,
                'current_medications': pr.current_medications,
                'emergency_contact_name': pr.emergency_contact_name,
                'emergency_contact_phone': pr.emergency_contact_phone,
                'patient_unique_id': pr.patient_unique_id,
            })
        except Exception:
            pass

        # Group by record type
        by_type = {}
        by_folder = {}
        active_allergies = []
        pending_followups = []
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_records = []

        for r in records_data:
            rt = r.get('record_type')
            by_type.setdefault(rt, []).append(r)

            folder = r.get('folder_name') or 'General'
            by_folder.setdefault(folder, []).append(r)

            if rt == 'ALLERGY' and r.get('allergy'):
                active_allergies.append(r)

            if r.get('requires_followup') and r.get('followup_date'):
                pending_followups.append(r)

            if r.get('record_date') and r['record_date'] >= str(thirty_days_ago):
                recent_records.append(r)

        critical_records = [r for r in records_data if r.get('severity_level') in ('CRITICAL', 'HIGH')]

        return Response({
            'generated_at': timezone.now(),
            'access_type': access_type,
            'patient': patient_info,
            'summary': {
                'total_records': len(records_data),
                'active_allergies': len(active_allergies),
                'pending_followups': len(pending_followups),
                'critical_or_high': len(critical_records),
                'recent_30_days': len(recent_records),
                'record_types': {k: len(v) for k, v in by_type.items()},
            },
            'medical_records': {
                'timeline': records_data,
                'by_type': by_type,
                'by_folder': by_folder,
                'critical_or_high': critical_records,
                'recent_30_days': recent_records,
                'pending_followups': pending_followups,
            },
            'active_allergies': active_allergies,
        })

    # ------------------------------------------------------------------
    # PDF export
    # ------------------------------------------------------------------

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """Export a single medical record as PDF."""
        record = self.get_object()
        if not MedicalRecordPDFService.is_available():
            return Response(
                {'error': 'PDF generation is not available. Install reportlab.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        include_attachments = request.query_params.get('include_attachments', 'false').lower() == 'true'
        try:
            pdf_buffer = MedicalRecordPDFService.generate_single_record_pdf(
                record, include_attachments=include_attachments
            )
            MedicalRecordAccessLog.objects.create(
                medical_record=record,
                accessed_by=request.user,
                access_type='PDF_EXPORT',
                ip_address=_get_client_ip(request),
            )
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="medical_record_{record.id}_{record.record_date}.pdf"'
            return response
        except Exception as e:
            return Response({'error': f'Failed to generate PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='export-summary')
    def export_summary(self, request):
        """Export all of the patient's active records as a summary PDF."""
        if request.user.role != UserRole.PATIENT:
            return Response(
                {'error': 'Only patients can export their own medical record summary.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not MedicalRecordPDFService.is_available():
            return Response(
                {'error': 'PDF generation is not available. Install reportlab.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            records = MedicalRecord.objects.filter(
                models.Q(patient=request.user) | models.Q(patient_record__linked_user=request.user),
                is_active=True,
            ).select_related('created_by').prefetch_related('prescription', 'allergy').order_by('-record_date')
            pdf_buffer = MedicalRecordPDFService.generate_patient_summary_pdf(request.user, records)
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="medical_records_summary_{request.user.id}.pdf"'
            return response
        except Exception as e:
            return Response({'error': f'Failed to generate PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# Provider Access viewset
# ---------------------------------------------------------------------------

class ProviderAccessViewSet(viewsets.ModelViewSet):
    """
    Manage provider access grants.

    Patients: grant/revoke access to their records.
    Providers: view their own grants.
    Admins: full control.

    POST  /api/medical-records/access/           - Grant access (or reactivate revoked grant)
    GET   /api/medical-records/access/my-providers/ - Providers with access (patient)
    GET   /api/medical-records/access/my-patients/  - Patients I can access (provider)
    POST  /api/medical-records/access/{id}/revoke/  - Revoke access
    POST  /api/medical-records/access/{id}/renew/   - Reactivate with optional new expiry
    """
    permission_classes = [IsAuthenticated, CanManageProviderAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active', 'access_type']
    ordering_fields = ['granted_at', 'expires_at']
    ordering = ['-granted_at']

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return ProviderAccess.objects.all().select_related('patient', 'provider__user')
        if user.role == UserRole.PATIENT:
            return ProviderAccess.objects.filter(patient=user).select_related('provider__user')
        if user.role == UserRole.PROVIDER:
            try:
                return ProviderAccess.objects.filter(
                    provider=user.provider_profile
                ).select_related('patient')
            except Exception:
                return ProviderAccess.objects.none()
        return ProviderAccess.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return ProviderAccessCreateSerializer
        return ProviderAccessSerializer

    def perform_create(self, serializer):
        serializer.save(access_granted_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='my-providers')
    def my_providers(self, request):
        """All providers who have (or had) access to my records — patient only."""
        if request.user.role != UserRole.PATIENT:
            return Response({'error': 'This endpoint is for patients only.'}, status=status.HTTP_403_FORBIDDEN)
        accesses = ProviderAccess.objects.filter(patient=request.user).select_related('provider__user')
        return Response(ProviderAccessSerializer(accesses, many=True).data)

    @action(detail=False, methods=['get'], url_path='my-patients')
    def my_patients(self, request):
        """All patients I have active access to — provider only."""
        if request.user.role != UserRole.PROVIDER:
            return Response({'error': 'This endpoint is for providers only.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            provider = request.user.provider_profile
        except Exception:
            return Response({'error': 'Provider profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        accesses = ProviderAccess.objects.filter(
            _valid_access_q(), provider=provider,
        ).select_related('patient')
        return Response(ProviderAccessSerializer(accesses, many=True).data)

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke an active access grant."""
        access = self.get_object()
        access.is_active = False
        access.save(update_fields=['is_active'])
        return Response({
            'message': 'Provider access revoked.',
            'access': ProviderAccessSerializer(access).data,
        })

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """
        Reactivate a revoked grant, optionally setting a new expiry.
        Body (optional): {"expires_at": "2026-12-31T00:00:00Z"}
        """
        access = self.get_object()
        access.is_active = True
        new_expiry = request.data.get('expires_at')
        if new_expiry:
            try:
                from django.utils.dateparse import parse_datetime
                parsed = parse_datetime(new_expiry)
                if parsed and parsed > timezone.now():
                    access.expires_at = parsed
                else:
                    return Response(
                        {'error': 'expires_at must be a valid future datetime.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Exception:
                return Response({'error': 'Invalid expires_at format.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            access.expires_at = None
        access.granted_at = timezone.now()
        access.save(update_fields=['is_active', 'expires_at', 'granted_at'])
        return Response({
            'message': 'Provider access renewed.',
            'access': ProviderAccessSerializer(access).data,
        })
