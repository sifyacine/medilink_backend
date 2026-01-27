"""
VTC views and viewsets.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from providers.models.vtc import VTC
from providers.serializers.vtc import VTCSerializer, VTCCreateSerializer
from common.permissions import IsVerifiedProvider


class VTCViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for VTC profiles.
    
    GET /api/provider/vtc/ - Get VTC profile
    PUT /api/provider/vtc/ - Update VTC profile
    PATCH /api/provider/vtc/ - Partial update VTC profile
    """
    serializer_class = VTCSerializer
    permission_classes = [IsAuthenticated, IsVerifiedProvider]
    
    def get_queryset(self):
        """Return VTC for authenticated provider."""
        try:
            provider = self.request.user.provider_profile
            if provider.provider_type == 'VTC':
                return VTC.objects.filter(provider=provider)
        except Exception:
            pass
        return VTC.objects.none()
    
    def get_object(self):
        """Get VTC profile for authenticated provider."""
        provider = self.request.user.provider_profile
        if provider.provider_type != 'VTC':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a VTC provider.')
        
        try:
            return provider.vtc_profile
        except VTC.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('VTC profile not found.')
    
    def perform_create(self, serializer):
        """Create VTC profile for authenticated provider."""
        provider = self.request.user.provider_profile
        if provider.provider_type != 'VTC':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a VTC provider.')
        
        # Check if profile already exists
        if hasattr(provider, 'vtc_profile'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError('VTC profile already exists.')
        
        serializer.save(provider=provider)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get VTC provider status.
        
        GET /api/provider/vtc/status/
        """
        try:
            provider = request.user.provider_profile
            if provider.provider_type != 'VTC':
                return Response(
                    {'error': 'You are not a VTC provider.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from providers.serializers.status import ProviderStatusSerializer
            return Response(ProviderStatusSerializer(provider).data)
        except Exception:
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
