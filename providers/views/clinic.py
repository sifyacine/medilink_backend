"""Clinic views and viewsets."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from providers.models.clinic import Clinic
from providers.serializers.clinic import ClinicSerializer, ClinicCreateSerializer
from common.permissions import IsVerifiedProvider, IsOwnerOrAdmin


class ClinicViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Clinic profiles.
    
    Standard router-generated endpoints (per-clinic, mostly for admin use):
    - GET /api/provider/clinic/{id}/
    - PUT /api/provider/clinic/{id}/
    - PATCH /api/provider/clinic/{id}/
    
    For the authenticated provider's own clinic profile without specifying an ID,
    use ClinicProfileView which exposes:
    - GET /api/provider/clinic/
    - PUT /api/provider/clinic/
    - PATCH /api/provider/clinic/
    """
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated, IsVerifiedProvider]
    
    def get_queryset(self):
        """Return clinic for authenticated provider."""
        try:
            provider = self.request.user.provider_profile
            if provider.provider_type == 'CLINIC':
                return Clinic.objects.filter(provider=provider)
        except Exception:
            pass
        return Clinic.objects.none()
    
    def get_object(self):
        """Get clinic profile for authenticated provider."""
        provider = self.request.user.provider_profile
        if provider.provider_type != 'CLINIC':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a clinic provider.')
        
        try:
            return provider.clinic_profile
        except Clinic.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Clinic profile not found.')
    
    def perform_create(self, serializer):
        """Create clinic profile for authenticated provider."""
        provider = self.request.user.provider_profile
        if provider.provider_type != 'CLINIC':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a clinic provider.')
        
        # Check if profile already exists
        if hasattr(provider, 'clinic_profile'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Clinic profile already exists.')
        
        serializer.save(provider=provider)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get clinic provider status.
        
        GET /api/provider/clinic/status/
        """
        try:
            provider = request.user.provider_profile
            if provider.provider_type != 'CLINIC':
                return Response(
                    {'error': 'You are not a clinic provider.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from providers.serializers.status import ProviderStatusSerializer
            return Response(ProviderStatusSerializer(provider).data)
        except Exception:
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class ClinicProfileView(APIView):
    """Single-endpoint clinic profile for the authenticated provider.

    Supports:
    - GET /api/provider/clinic/
    - PUT /api/provider/clinic/
    - PATCH /api/provider/clinic/
    """

    permission_classes = [IsAuthenticated, IsVerifiedProvider]

    def _get_provider(self, request):
        return request.user.provider_profile

    def _get_clinic_instance(self, request):
        provider = self._get_provider(request)
        if provider.provider_type != 'CLINIC':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a clinic provider.')

        try:
            return provider.clinic_profile
        except Clinic.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Clinic profile not found.')

    def get(self, request, *args, **kwargs):
        clinic = self._get_clinic_instance(request)
        serializer = ClinicSerializer(clinic, context={"request": request})
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        clinic = self._get_clinic_instance(request)
        serializer = ClinicSerializer(clinic, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        clinic = self._get_clinic_instance(request)
        serializer = ClinicSerializer(
            clinic,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

