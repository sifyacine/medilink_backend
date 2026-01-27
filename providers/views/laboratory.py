"""
Laboratory views and viewsets.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from providers.models.laboratory import Laboratory
from providers.serializers.laboratory import LaboratorySerializer, LaboratoryCreateSerializer
from common.permissions import IsVerifiedProvider


class LaboratoryViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Laboratory profiles.
    
    GET /api/provider/laboratory/ - Get laboratory profile
    PUT /api/provider/laboratory/ - Update laboratory profile
    PATCH /api/provider/laboratory/ - Partial update laboratory profile
    """
    serializer_class = LaboratorySerializer
    permission_classes = [IsAuthenticated, IsVerifiedProvider]
    
    def get_queryset(self):
        """Return laboratory for authenticated provider."""
        try:
            provider = self.request.user.provider_profile
            if provider.provider_type == 'LABORATORY':
                return Laboratory.objects.filter(provider=provider)
        except Exception:
            pass
        return Laboratory.objects.none()
    
    def get_object(self):
        """Get laboratory profile for authenticated provider."""
        provider = self.request.user.provider_profile
        if provider.provider_type != 'LABORATORY':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a laboratory provider.')
        
        try:
            return provider.laboratory_profile
        except Laboratory.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Laboratory profile not found.')
    
    def perform_create(self, serializer):
        """Create laboratory profile for authenticated provider."""
        provider = self.request.user.provider_profile
        if provider.provider_type != 'LABORATORY':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a laboratory provider.')
        
        # Check if profile already exists
        if hasattr(provider, 'laboratory_profile'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Laboratory profile already exists.')
        
        serializer.save(provider=provider)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get laboratory provider status.
        
        GET /api/provider/laboratory/status/
        """
        try:
            provider = request.user.provider_profile
            if provider.provider_type != 'LABORATORY':
                return Response(
                    {'error': 'You are not a laboratory provider.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from providers.serializers.status import ProviderStatusSerializer
            return Response(ProviderStatusSerializer(provider).data)
        except Exception:
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
