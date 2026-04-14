"""
Prescription views for the Medilink platform.

This module provides API endpoints for prescription management:
- Doctor creates prescriptions for completed appointments
- Patient views their prescription history
- PDF upload (frontend generates PDF)
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, Max
from django.shortcuts import get_object_or_404

from .models import Prescription, PrescriptionItem, PrescriptionStatus, MedicationType, DosageFrequency
from .serializers import (
    PrescriptionListSerializer,
    PrescriptionDetailSerializer,
    PrescriptionCreateSerializer,
    PrescriptionUpdateSerializer,
    PrescriptionPDFUploadSerializer,
    PrescriptionItemSerializer,
    PrescriptionItemCreateSerializer,
)
from .permissions import (
    IsDoctorUser,
    IsPrescriptionDoctor,
    CanViewPrescription,
    CanModifyPrescription,
    get_doctor_from_user,
)


class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for prescription management.
    
    Endpoints:
    - POST /api/prescriptions/ - Create prescription (doctor only)
    - GET /api/prescriptions/ - List prescriptions (filtered by role)
    - GET /api/prescriptions/{id}/ - Get prescription details
    - PUT/PATCH /api/prescriptions/{id}/ - Update prescription (draft only)
    - DELETE /api/prescriptions/{id}/ - Delete prescription (draft only)
    
    Actions:
    - POST /api/prescriptions/{id}/upload-pdf/ - Upload PDF
    - POST /api/prescriptions/{id}/issue/ - Issue prescription
    - POST /api/prescriptions/{id}/cancel/ - Cancel prescription
    - GET /api/prescriptions/{id}/items/ - List items
    - POST /api/prescriptions/{id}/items/ - Add item
    - GET /api/prescriptions/my-prescriptions/ - Patient's prescriptions
    - GET /api/prescriptions/my-issued/ - Doctor's issued prescriptions
    - GET /api/prescriptions/choices/ - Get enum choices
    """
    queryset = Prescription.objects.all()
    
    ALLOWED_ORDERING_FIELDS = {
        'created_at', '-created_at',
        'issued_at', '-issued_at',
        'valid_until', '-valid_until',
        'status', '-status',
        'updated_at', '-updated_at',
    }
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsDoctorUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, CanModifyPrescription]
        elif self.action in ['upload_pdf', 'issue', 'cancel']:
            permission_classes = [permissions.IsAuthenticated, IsPrescriptionDoctor]
        elif self.action == 'items':
            if self.request.method == 'POST':
                permission_classes = [permissions.IsAuthenticated, IsPrescriptionDoctor]
            else:
                permission_classes = [permissions.IsAuthenticated, CanViewPrescription]
        elif self.action in ['retrieve', 'list']:
            permission_classes = [permissions.IsAuthenticated, CanViewPrescription]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return PrescriptionListSerializer
        elif self.action == 'create':
            return PrescriptionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PrescriptionUpdateSerializer
        elif self.action == 'upload_pdf':
            return PrescriptionPDFUploadSerializer
        elif self.action in ['items', 'add_item']:
            return PrescriptionItemSerializer
        return PrescriptionDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        queryset = Prescription.objects.select_related(
            'doctor', 'patient', 'patient_record', 'clinic', 'appointment'
        ).prefetch_related('items')
        
        if user.is_staff or user.is_superuser:
            return queryset
        
        # Doctor sees their own prescriptions
        # Relationship: User -> provider_profile (Provider) -> doctor_profile (Doctor)
        doctor = None
        try:
            provider = getattr(user, 'provider_profile', None)
            if provider:
                doctor = getattr(provider, 'doctor_profile', None)
        except Exception:
            pass
        
        if doctor:
            return queryset.filter(doctor=doctor)
        
        # Patient sees their own prescriptions
        return queryset.filter(
            Q(patient=user) |
            Q(patient_record__linked_user=user)
        )
    
    @action(detail=True, methods=['post'], url_path='upload-pdf',
            parser_classes=[MultiPartParser, FormParser])
    def upload_pdf(self, request, pk=None):
        """
        Upload PDF file for a prescription.
        
        POST /api/prescriptions/{id}/upload-pdf/
        Content-Type: multipart/form-data
        
        Body: { "pdf_file": <file> }
        """
        prescription = self.get_object()
        
        serializer = PrescriptionPDFUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        prescription.pdf_file = serializer.validated_data['pdf_file']
        prescription.save(update_fields=['pdf_file', 'updated_at'])
        
        return Response(
            PrescriptionDetailSerializer(prescription, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        """
        Issue a prescription (change from draft to issued).
        
        POST /api/prescriptions/{id}/issue/
        """
        prescription = self.get_object()
        
        try:
            prescription.issue()
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            PrescriptionDetailSerializer(prescription, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a prescription.
        
        POST /api/prescriptions/{id}/cancel/
        """
        prescription = self.get_object()
        
        try:
            prescription.cancel()
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            PrescriptionDetailSerializer(prescription, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get', 'post'])
    def items(self, request, pk=None):
        """
        List or add prescription items.
        
        GET /api/prescriptions/{id}/items/ - List items
        POST /api/prescriptions/{id}/items/ - Add item
        """
        prescription = self.get_object()
        
        if request.method == 'GET':
            items = prescription.items.all()
            serializer = PrescriptionItemSerializer(items, many=True)
            return Response(serializer.data)
        
        # POST - add item
        if prescription.status != PrescriptionStatus.DRAFT:
            return Response(
                {'error': 'Can only add items to draft prescriptions.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PrescriptionItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get next order
        max_order = prescription.items.aggregate(max_order=Max('order'))['max_order'] or 0
        
        item = PrescriptionItem.objects.create(
            prescription=prescription,
            order=max_order + 1,
            **serializer.validated_data
        )
        
        return Response(
            PrescriptionItemSerializer(item).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], url_path='my-prescriptions')
    def my_prescriptions(self, request):
        """
        Get current user's prescriptions (patient view).
        
        GET /api/prescriptions/my-prescriptions/
        
        Query params:
        - status: Filter by status
        - ordering: Order by field (default: -created_at)
        """
        user = request.user
        
        queryset = Prescription.objects.filter(
            Q(patient=user) |
            Q(patient_record__linked_user=user)
        ).select_related(
            'doctor', 'clinic', 'appointment'
        ).prefetch_related('items')
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        if ordering not in self.ALLOWED_ORDERING_FIELDS:
            ordering = '-created_at'
        queryset = queryset.order_by(ordering)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PrescriptionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PrescriptionListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-issued')
    def my_issued(self, request):
        """
        Get prescriptions issued by current doctor.
        
        GET /api/prescriptions/my-issued/
        
        Query params:
        - status: Filter by status
        - patient_id: Filter by patient
        - from_date: From date (YYYY-MM-DD)
        - to_date: To date (YYYY-MM-DD)
        - ordering: Order by field (default: -created_at)
        """
        # Get doctor using correct relationship chain
        doctor = None
        try:
            provider = getattr(request.user, 'provider_profile', None)
            if provider:
                doctor = getattr(provider, 'doctor_profile', None)
        except Exception:
            pass
        
        if not doctor:
            return Response(
                {'error': 'Only doctors can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = Prescription.objects.filter(
            doctor=doctor
        ).select_related(
            'patient', 'patient_record', 'clinic', 'appointment'
        ).prefetch_related('items')
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by patient
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(
                Q(patient_id=patient_id) |
                Q(patient_record_id=patient_id) |
                Q(patient_record__linked_user_id=patient_id)
            )
        
        # Filter by date range
        from_date = request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        
        to_date = request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)
        
        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        if ordering not in self.ALLOWED_ORDERING_FIELDS:
            ordering = '-created_at'
        queryset = queryset.order_by(ordering)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PrescriptionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PrescriptionListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def choices(self, request):
        """
        Get enum choices for frontend.
        
        GET /api/prescriptions/choices/
        """
        return Response({
            'status': [
                {'value': choice[0], 'label': choice[1]}
                for choice in PrescriptionStatus.choices
            ],
            'medication_type': [
                {'value': choice[0], 'label': choice[1]}
                for choice in MedicationType.choices
            ],
            'dosage_frequency': [
                {'value': choice[0], 'label': choice[1]}
                for choice in DosageFrequency.choices
            ],
        })


class PrescriptionItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing individual prescription items.
    
    Used for updating or deleting specific items.
    """
    queryset = PrescriptionItem.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'create']:
            return PrescriptionItemCreateSerializer
        return PrescriptionItemSerializer
    
    def get_queryset(self):
        """Filter to items the user can access."""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return PrescriptionItem.objects.all()
        
        # Doctor sees items from their prescriptions
        # Use correct relationship chain: User -> provider_profile -> doctor_profile
        doctor = None
        try:
            provider = getattr(user, 'provider_profile', None)
            if provider:
                doctor = getattr(provider, 'doctor_profile', None)
        except Exception:
            pass
        
        if doctor:
            return PrescriptionItem.objects.filter(
                prescription__doctor=doctor
            )
        
        # Patient sees their items
        return PrescriptionItem.objects.filter(
            Q(prescription__patient=user) |
            Q(prescription__patient_record__linked_user=user)
        )
    
    def destroy(self, request, *args, **kwargs):
        """Only allow deletion of items from draft prescriptions."""
        item = self.get_object()
        
        if item.prescription.status != PrescriptionStatus.DRAFT:
            return Response(
                {'error': 'Can only delete items from draft prescriptions.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Only allow updates to items from draft prescriptions."""
        item = self.get_object()
        
        if item.prescription.status != PrescriptionStatus.DRAFT:
            return Response(
                {'error': 'Can only update items from draft prescriptions.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Only allow creating items on draft prescriptions."""
        prescription_id = request.data.get('prescription')
        if not prescription_id:
            return Response(
                {'prescription': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        prescription = get_object_or_404(Prescription, pk=prescription_id)

        if prescription.status != PrescriptionStatus.DRAFT:
            return Response(
                {'error': 'Can only add items to draft prescriptions.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        if not (user.is_staff or user.is_superuser):
            doctor = get_doctor_from_user(user)
            if not doctor or prescription.doctor != doctor:
                return Response(
                    {'error': 'You can only add items to your own prescriptions.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        item_payload = request.data.copy()
        item_payload.pop('prescription', None)
        serializer = self.get_serializer(data=item_payload)
        serializer.is_valid(raise_exception=True)

        max_order = prescription.items.aggregate(max_order=Max('order'))['max_order'] or 0
        item = PrescriptionItem.objects.create(
            prescription=prescription,
            order=serializer.validated_data.get('order', max_order + 1),
            **serializer.validated_data
        )

        return Response(PrescriptionItemSerializer(item).data, status=status.HTTP_201_CREATED)
