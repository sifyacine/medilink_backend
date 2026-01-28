"""
Views for Patient Records app.

Provides endpoints for:
- Providers to create/manage patient records
- Patients to link their accounts to existing records
- Managing provider access to patient records
- Secure medical record sharing via tokens
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from patients.models import PatientRecord, ProviderPatientAccess, MedicalRecordShareToken, ShareTokenAccessLog
from patients.serializers import (
    PatientRecordSerializer,
    PatientRecordCreateSerializer,
    PatientRecordUpdateSerializer,
    PatientRecordListSerializer,
    LinkingTokenSerializer,
    LinkPatientAccountSerializer,
    ProviderPatientAccessSerializer,
    GrantAccessSerializer,
    CreateShareTokenSerializer,
    ShareTokenSerializer,
    ShareTokenListSerializer,
    ShareTokenAccessLogSerializer,
    UseShareTokenSerializer,
    PatientMedicalHistorySerializer,
)
from patients.permissions import (
    IsVerifiedProvider,
    CanAccessPatientRecord,
    CanModifyPatientRecord,
    CanLinkPatientAccount,
)
from common.enums import UserRole


class PatientRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patient records.
    
    Providers can:
    - Create patient records for patients without accounts
    - View patient records they have access to
    - Update patient records they created or have FULL access to
    
    Patients can:
    - View their linked patient record
    
    GET /api/patients/ - List patient records (filtered by access)
    POST /api/patients/ - Create patient record (providers only)
    GET /api/patients/{id}/ - Get patient record details
    PUT /api/patients/{id}/ - Update patient record
    DELETE /api/patients/{id}/ - Soft delete (deactivate) patient record
    
    Special endpoints:
    GET /api/patients/{id}/token/ - Get linking token (provider only)
    POST /api/patients/{id}/regenerate-token/ - Regenerate linking token
    POST /api/patients/{id}/grant-access/ - Grant access to another provider
    """
    queryset = PatientRecord.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'blood_type', 'is_active', 'city', 'country']
    search_fields = ['first_name', 'last_name', 'phone_number', 'email', 'national_id']
    ordering_fields = ['first_name', 'last_name', 'date_of_birth', 'created_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Return permissions based on action.
        """
        if self.action == 'create':
            # Only verified providers can create patient records
            return [IsAuthenticated(), IsVerifiedProvider()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanAccessPatientRecord(), CanModifyPatientRecord()]
        elif self.action in ['token', 'regenerate_token', 'grant_access']:
            return [IsAuthenticated(), IsVerifiedProvider()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PatientRecordCreateSerializer
        elif self.action == 'list':
            return PatientRecordListSerializer
        elif self.action in ['update', 'partial_update']:
            return PatientRecordUpdateSerializer
        return PatientRecordSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user role and access permissions.
        
        - Patients: Only see their linked record
        - Providers: See records they created or have access to
        - Admins: See all records
        """
        queryset = PatientRecord.objects.filter(is_active=True)
        user = self.request.user
        
        if user.role == UserRole.ADMIN:
            return queryset
        
        if user.role == UserRole.PATIENT:
            # Patients can only see their linked record
            return queryset.filter(linked_user=user)
        
        if user.role == UserRole.PROVIDER:
            try:
                provider = user.provider_profile
                
                # Get records created by this provider
                created_records = queryset.filter(created_by_provider=provider)
                
                # Get records with explicit access
                access_record_ids = ProviderPatientAccess.objects.filter(
                    provider=provider
                ).values_list('patient_record_id', flat=True)
                
                access_records = queryset.filter(id__in=access_record_ids)
                
                return (created_records | access_records).distinct()
                
            except Exception:
                return queryset.none()
        
        return queryset.none()
    
    def perform_create(self, serializer):
        """
        Create a patient record and set up provider access.
        """
        user = self.request.user
        provider = user.provider_profile
        
        # Create the patient record
        patient_record = serializer.save(created_by_provider=provider)
        
        # Automatically grant FULL access to the creating provider
        ProviderPatientAccess.objects.create(
            provider=provider,
            patient_record=patient_record,
            access_level='FULL',
            granted_by=provider
        )
        
        return patient_record
    
    def perform_destroy(self, instance):
        """Soft delete - set is_active to False instead of deleting."""
        instance.is_active = False
        instance.save(update_fields=['is_active'])
    
    @action(detail=True, methods=['get'], url_path='token')
    def token(self, request, pk=None):
        """
        Get the linking token for a patient record.
        
        This is used by providers to give the token to patients
        so they can link their accounts later.
        
        Only providers who created the record or have FULL access
        can retrieve the token.
        """
        patient_record = self.get_object()
        
        # Check if user has permission to see the token
        user = request.user
        if user.role == UserRole.PROVIDER:
            try:
                provider = user.provider_profile
                
                # Check if creator or has FULL access
                has_access = (
                    patient_record.created_by_provider == provider or
                    ProviderPatientAccess.objects.filter(
                        provider=provider,
                        patient_record=patient_record,
                        access_level='FULL'
                    ).exists()
                )
                
                if not has_access:
                    return Response(
                        {'error': 'You do not have permission to view this token.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                    
            except Exception:
                return Response(
                    {'error': 'Provider profile not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if patient_record.token_used or patient_record.is_linked:
            return Response({
                'linking_token': None,
                'patient_name': patient_record.full_name,
                'token_used': patient_record.token_used,
                'is_linked': patient_record.is_linked,
                'message': 'Token has already been used or record is linked.'
            })
        
        return Response({
            'linking_token': patient_record.linking_token,
            'patient_name': patient_record.full_name,
            'token_used': patient_record.token_used,
            'is_linked': patient_record.is_linked,
        })
    
    @action(detail=True, methods=['post'], url_path='regenerate-token')
    def regenerate_token(self, request, pk=None):
        """
        Regenerate the linking token for a patient record.
        
        Use this if the token was lost or needs to be reissued.
        Only the creator can regenerate the token.
        """
        patient_record = self.get_object()
        
        # Only creator can regenerate
        user = request.user
        try:
            provider = user.provider_profile
            if patient_record.created_by_provider != provider:
                return Response(
                    {'error': 'Only the record creator can regenerate the token.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cannot regenerate if already linked
        if patient_record.is_linked:
            return Response(
                {'error': 'Cannot regenerate token for a linked record.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_token = patient_record.regenerate_token()
        
        return Response({
            'linking_token': new_token,
            'patient_name': patient_record.full_name,
            'message': 'Token has been regenerated.'
        })
    
    @action(detail=True, methods=['post'], url_path='grant-access')
    def grant_access(self, request, pk=None):
        """
        Grant another provider access to this patient record.
        
        Only the creator or providers with FULL access can grant access.
        """
        patient_record = self.get_object()
        
        serializer = GrantAccessSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has permission to grant access
        user = request.user
        try:
            granting_provider = user.provider_profile
            
            has_permission = (
                patient_record.created_by_provider == granting_provider or
                ProviderPatientAccess.objects.filter(
                    provider=granting_provider,
                    patient_record=patient_record,
                    access_level='FULL'
                ).exists()
            )
            
            if not has_permission:
                return Response(
                    {'error': 'You do not have permission to grant access.'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        except Exception:
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the provider to grant access to
        from providers.models.provider import Provider
        try:
            target_provider = Provider.objects.get(pk=serializer.validated_data['provider_id'])
        except Provider.DoesNotExist:
            return Response(
                {'error': 'Target provider not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if access already exists
        access, created = ProviderPatientAccess.objects.get_or_create(
            provider=target_provider,
            patient_record=patient_record,
            defaults={
                'access_level': serializer.validated_data['access_level'],
                'granted_by': granting_provider
            }
        )
        
        if not created:
            # Update existing access
            access.access_level = serializer.validated_data['access_level']
            access.granted_by = granting_provider
            access.save()
        
        return Response(
            ProviderPatientAccessSerializer(access).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanLinkPatientAccount])
def link_patient_account(request):
    """
    Link a patient account to an existing patient record.
    
    This endpoint is used when a patient:
    1. Creates a new Medilink account
    2. Has a linking token from a healthcare provider
    3. Wants to link their existing medical records to their new account
    
    POST /api/patients/link-account/
    Body: {
        "linking_token": "abc123..."
    }
    
    Returns:
    - The linked patient record information
    - Confirmation of successful linking
    
    Errors:
    - Invalid token
    - Token already used
    - Record already linked
    - User already has a linked record
    """
    serializer = LinkPatientAccountSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['linking_token']
    
    try:
        patient_record = PatientRecord.objects.get(linking_token=token)
    except PatientRecord.DoesNotExist:
        return Response(
            {'error': 'Invalid linking token.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user already has a linked patient record
    user = request.user
    if hasattr(user, 'patient_record') and user.patient_record is not None:
        return Response(
            {'error': 'Your account is already linked to a patient record.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        patient_record.link_to_user(user)
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'message': 'Account successfully linked to patient record.',
        'patient_record': PatientRecordSerializer(patient_record).data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_patient_record(request):
    """
    Get the current user's linked patient record.
    
    GET /api/patients/me/
    
    Returns:
    - Patient record if linked
    - 404 if no linked record
    """
    user = request.user
    
    if user.role != UserRole.PATIENT:
        return Response(
            {'error': 'Only patients can access this endpoint.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        patient_record = PatientRecord.objects.get(linked_user=user)
        return Response(PatientRecordSerializer(patient_record).data)
    except PatientRecord.DoesNotExist:
        return Response(
            {'error': 'No linked patient record found.'},
            status=status.HTTP_404_NOT_FOUND
        )


# =============================================================================
# SHARE TOKEN VIEWS
# =============================================================================

class ShareTokenViewSet(viewsets.ViewSet):
    """
    ViewSet for managing medical record share tokens.
    
    Patients can:
    - Create share tokens for their records
    - List their active share tokens
    - Revoke share tokens
    - View access logs
    
    Providers can:
    - Use share tokens to access patient records
    """
    permission_classes = [IsAuthenticated]
    
    def get_patient_record(self, request):
        """Get the patient record for the current user."""
        user = request.user
        if user.role != UserRole.PATIENT:
            return None
        try:
            return PatientRecord.objects.get(linked_user=user)
        except PatientRecord.DoesNotExist:
            return None
    
    def list(self, request):
        """
        List all share tokens for the current patient.
        
        GET /api/patients/share-tokens/
        
        Query params:
        - active_only: bool - Only show active/usable tokens
        """
        patient_record = self.get_patient_record(request)
        if not patient_record:
            return Response(
                {'error': 'Only linked patients can access share tokens.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tokens = MedicalRecordShareToken.objects.filter(
            patient_record=patient_record
        ).order_by('-created_at')
        
        # Filter by active status if requested
        active_only = request.query_params.get('active_only', '').lower() == 'true'
        if active_only:
            tokens = [t for t in tokens if t.is_usable]
        
        serializer = ShareTokenListSerializer(tokens, many=True)
        return Response({
            'count': len(serializer.data),
            'tokens': serializer.data
        })
    
    def create(self, request):
        """
        Create a new share token.
        
        POST /api/patients/share-tokens/
        Body: {
            "access_level": "READ_ONLY",
            "expires_in_hours": 24,
            "max_uses": 1,
            "target_provider_id": null,
            "notes": "For Dr. Smith"
        }
        """
        patient_record = self.get_patient_record(request)
        if not patient_record:
            return Response(
                {'error': 'Only linked patients can create share tokens.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CreateShareTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Calculate expiry
        expires_at = timezone.now() + timedelta(hours=data['expires_in_hours'])
        
        # Get target provider if specified
        target_provider = None
        if data.get('target_provider_id'):
            from providers.models.provider import Provider
            target_provider = Provider.objects.get(pk=data['target_provider_id'])
        
        # Create the token
        share_token = MedicalRecordShareToken.objects.create(
            patient_record=patient_record,
            created_by_user=request.user,
            access_level=data['access_level'],
            expires_at=expires_at,
            max_uses=data['max_uses'],
            target_provider=target_provider,
            notes=data.get('notes', ''),
        )
        
        response_serializer = ShareTokenSerializer(
            share_token,
            context={'request': request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """
        Get details of a specific share token.
        
        GET /api/patients/share-tokens/{id}/
        """
        patient_record = self.get_patient_record(request)
        if not patient_record:
            return Response(
                {'error': 'Only linked patients can access share tokens.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            token = MedicalRecordShareToken.objects.get(
                pk=pk,
                patient_record=patient_record
            )
        except MedicalRecordShareToken.DoesNotExist:
            return Response(
                {'error': 'Share token not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ShareTokenSerializer(token, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='revoke')
    def revoke(self, request, pk=None):
        """
        Revoke a share token.
        
        POST /api/patients/share-tokens/{id}/revoke/
        """
        patient_record = self.get_patient_record(request)
        if not patient_record:
            return Response(
                {'error': 'Only linked patients can revoke share tokens.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            token = MedicalRecordShareToken.objects.get(
                pk=pk,
                patient_record=patient_record
            )
        except MedicalRecordShareToken.DoesNotExist:
            return Response(
                {'error': 'Share token not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if token.is_revoked:
            return Response(
                {'error': 'Token is already revoked.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token.revoke()
        
        return Response({
            'message': 'Share token has been revoked.',
            'token_id': token.id
        })
    
    @action(detail=True, methods=['get'], url_path='access-logs')
    def access_logs(self, request, pk=None):
        """
        Get access logs for a specific share token.
        
        GET /api/patients/share-tokens/{id}/access-logs/
        """
        patient_record = self.get_patient_record(request)
        if not patient_record:
            return Response(
                {'error': 'Only linked patients can view access logs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            token = MedicalRecordShareToken.objects.get(
                pk=pk,
                patient_record=patient_record
            )
        except MedicalRecordShareToken.DoesNotExist:
            return Response(
                {'error': 'Share token not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        logs = ShareTokenAccessLog.objects.filter(share_token=token)
        serializer = ShareTokenAccessLogSerializer(logs, many=True)
        
        return Response({
            'token_id': token.id,
            'use_count': token.use_count,
            'logs': serializer.data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def access_via_share_token(request, token):
    """
    Access patient records via a share token.
    
    GET /api/patients/records/share/{token}/
    
    This endpoint is used by providers to access patient records
    using a share token given to them by the patient.
    
    Returns:
    - Patient information (based on access level)
    - Medical records summary
    """
    user = request.user
    
    # Only providers can use share tokens
    if user.role != UserRole.PROVIDER:
        return Response(
            {'error': 'Only providers can access records via share tokens.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get the provider
    try:
        provider = user.provider_profile
    except Exception:
        return Response(
            {'error': 'Provider profile not found.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find and validate the share token
    try:
        share_token = MedicalRecordShareToken.objects.get(token=token)
    except MedicalRecordShareToken.DoesNotExist:
        return Response(
            {'error': 'Invalid share token.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if token is usable
    if not share_token.is_usable:
        if share_token.is_revoked:
            error = 'This share token has been revoked.'
        elif share_token.is_expired:
            error = 'This share token has expired.'
        else:
            error = 'This share token is no longer valid.'
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if token is targeted to a specific provider
    if share_token.target_provider and share_token.target_provider != provider:
        return Response(
            {'error': 'This share token is for a different provider.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Record the use
    ip_address = request.META.get('REMOTE_ADDR')
    share_token.record_use(provider)
    
    # Update the access log with IP
    latest_log = ShareTokenAccessLog.objects.filter(
        share_token=share_token
    ).order_by('-accessed_at').first()
    if latest_log:
        latest_log.ip_address = ip_address
        latest_log.save(update_fields=['ip_address'])
    
    # Get the patient record
    patient_record = share_token.patient_record
    
    # Get medical records based on access level
    from medical_record.models import MedicalRecord
    medical_records = MedicalRecord.objects.filter(
        patient_record=patient_record,
        is_active=True
    ).order_by('-record_date')
    
    # For LIMITED access, exclude confidential records
    if share_token.access_level == 'LIMITED':
        medical_records = medical_records.filter(is_confidential=False)
    
    # Build response based on access level
    response_data = {
        'access_level': share_token.access_level,
        'token_id': share_token.id,
        'uses_remaining': max(0, share_token.max_uses - share_token.use_count) if share_token.max_uses > 0 else 'unlimited',
        'expires_at': share_token.expires_at.isoformat(),
    }
    
    # Patient info (always included)
    response_data['patient'] = {
        'patient_unique_id': patient_record.patient_unique_id,
        'full_name': patient_record.full_name,
        'date_of_birth': str(patient_record.date_of_birth),
        'age': patient_record.age,
        'gender': patient_record.gender,
        'blood_type': patient_record.blood_type,
    }
    
    # Add more info for FULL or READ_ONLY access
    if share_token.access_level in ['FULL', 'READ_ONLY']:
        response_data['patient']['known_allergies'] = patient_record.known_allergies
        response_data['patient']['chronic_conditions'] = patient_record.chronic_conditions
        response_data['patient']['current_medications'] = patient_record.current_medications
        response_data['patient']['emergency_contact_name'] = patient_record.emergency_contact_name
        response_data['patient']['emergency_contact_phone'] = patient_record.emergency_contact_phone
    
    # Medical records summary
    records_data = []
    for record in medical_records[:50]:  # Limit to 50 most recent
        record_info = {
            'id': record.id,
            'title': record.title,
            'record_type': record.record_type,
            'record_date': str(record.record_date),
            'is_confidential': record.is_confidential,
        }
        
        # Include more details for FULL access
        if share_token.access_level == 'FULL':
            record_info['description'] = record.description
            record_info['symptoms'] = record.symptoms
            record_info['diagnosis_code'] = record.diagnosis_code
        
        records_data.append(record_info)
    
    response_data['medical_records'] = {
        'count': medical_records.count(),
        'records': records_data
    }
    
    # Optionally grant temporary access to the provider
    # (for FULL access tokens, this allows the provider to access specific records)
    if share_token.access_level == 'FULL':
        # Create or update provider access
        ProviderPatientAccess.objects.update_or_create(
            provider=provider,
            patient_record=patient_record,
            defaults={
                'access_level': 'READ_ONLY',  # Share token grants read-only access
                'granted_by': None,  # Auto-granted via token
            }
        )
        response_data['access_granted'] = True
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_share_tokens(request):
    """
    Get all share tokens for the current patient.
    Convenience alias for ShareTokenViewSet.list()
    
    GET /api/patients/my-share-tokens/
    """
    user = request.user
    
    if user.role != UserRole.PATIENT:
        return Response(
            {'error': 'Only patients can access share tokens.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        patient_record = PatientRecord.objects.get(linked_user=user)
    except PatientRecord.DoesNotExist:
        return Response(
            {'error': 'No linked patient record found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get query params
    active_only = request.query_params.get('active_only', '').lower() == 'true'
    
    tokens = MedicalRecordShareToken.objects.filter(
        patient_record=patient_record
    ).order_by('-created_at')
    
    if active_only:
        tokens = [t for t in tokens if t.is_usable]
    
    serializer = ShareTokenSerializer(tokens, many=True, context={'request': request})
    
    return Response({
        'count': len(serializer.data),
        'tokens': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_medical_records(request):
    """
    Get medical records for the current patient.
    
    GET /api/patients/my-records/
    
    Query params:
    - record_type: Filter by type (DIAGNOSIS, PRESCRIPTION, etc.)
    - limit: Max records to return (default 50)
    """
    user = request.user
    
    if user.role != UserRole.PATIENT:
        return Response(
            {'error': 'Only patients can access this endpoint.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        patient_record = PatientRecord.objects.get(linked_user=user)
    except PatientRecord.DoesNotExist:
        return Response(
            {'error': 'No linked patient record found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    from medical_record.models import MedicalRecord
    
    # Get records linked to this patient
    records = MedicalRecord.objects.filter(
        patient_record=patient_record,
        is_active=True
    ).order_by('-record_date')
    
    # Also get records linked to the user directly
    user_records = MedicalRecord.objects.filter(
        patient=user,
        is_active=True
    ).order_by('-record_date')
    
    # Combine and deduplicate
    all_records = (records | user_records).distinct().order_by('-record_date')
    
    # Filter by type if specified
    record_type = request.query_params.get('record_type')
    if record_type:
        all_records = all_records.filter(record_type=record_type)
    
    # Limit results
    limit = min(int(request.query_params.get('limit', 50)), 100)
    all_records = all_records[:limit]
    
    # Build response
    records_data = []
    for record in all_records:
        records_data.append({
            'id': record.id,
            'title': record.title,
            'record_type': record.record_type,
            'record_date': str(record.record_date),
            'description': record.description,
            'diagnosis_code': record.diagnosis_code,
            'symptoms': record.symptoms,
            'is_confidential': record.is_confidential,
            'requires_followup': record.requires_followup,
            'followup_date': str(record.followup_date) if record.followup_date else None,
            'created_at': record.created_at.isoformat(),
        })
    
    return Response({
        'patient_unique_id': patient_record.patient_unique_id,
        'patient_name': patient_record.full_name,
        'count': len(records_data),
        'records': records_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_medical_history(request, patient_id):
    """
    Get complete medical history for a patient.
    For providers with access to the patient.
    
    GET /api/patients/{patient_id}/history/
    """
    user = request.user
    
    # Only providers can access this
    if user.role != UserRole.PROVIDER:
        return Response(
            {'error': 'Only providers can access patient history.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        provider = user.provider_profile
    except Exception:
        return Response(
            {'error': 'Provider profile not found.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get the patient record
    try:
        patient_record = PatientRecord.objects.get(pk=patient_id)
    except PatientRecord.DoesNotExist:
        return Response(
            {'error': 'Patient record not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check access
    has_access = (
        patient_record.created_by_provider == provider or
        ProviderPatientAccess.objects.filter(
            provider=provider,
            patient_record=patient_record
        ).exists()
    )
    
    if not has_access:
        return Response(
            {'error': 'You do not have access to this patient.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get medical records
    from medical_record.models import MedicalRecord
    
    records = MedicalRecord.objects.filter(
        patient_record=patient_record,
        is_active=True
    ).order_by('-record_date')
    
    # Build comprehensive response
    response_data = {
        'patient': {
            'id': patient_record.id,
            'patient_unique_id': patient_record.patient_unique_id,
            'full_name': patient_record.full_name,
            'date_of_birth': str(patient_record.date_of_birth),
            'age': patient_record.age,
            'gender': patient_record.gender,
            'blood_type': patient_record.blood_type,
            'known_allergies': patient_record.known_allergies,
            'chronic_conditions': patient_record.chronic_conditions,
            'current_medications': patient_record.current_medications,
            'emergency_contact_name': patient_record.emergency_contact_name,
            'emergency_contact_phone': patient_record.emergency_contact_phone,
        },
        'medical_history': {
            'total_records': records.count(),
            'by_type': {},
        }
    }
    
    # Group records by type
    for record in records:
        record_type = record.record_type
        if record_type not in response_data['medical_history']['by_type']:
            response_data['medical_history']['by_type'][record_type] = []
        
        response_data['medical_history']['by_type'][record_type].append({
            'id': record.id,
            'title': record.title,
            'record_date': str(record.record_date),
            'description': record.description,
            'diagnosis_code': record.diagnosis_code,
            'symptoms': record.symptoms,
            'is_confidential': record.is_confidential,
            'requires_followup': record.requires_followup,
            'created_at': record.created_at.isoformat(),
        })
    
    return Response(response_data)
