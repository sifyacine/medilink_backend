"""
Seller views and viewsets.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from providers.models.seller import Seller
from providers.serializers.seller import SellerSerializer, SellerCreateSerializer
from common.permissions import IsVerifiedProvider


class SellerViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Seller profiles.
    
    GET /api/provider/seller/ - Get seller profile
    PUT /api/provider/seller/ - Update seller profile
    PATCH /api/provider/seller/ - Partial update seller profile
    """
    serializer_class = SellerSerializer
    permission_classes = [IsAuthenticated, IsVerifiedProvider]
    
    def get_queryset(self):
        """Return seller for authenticated provider."""
        try:
            provider = self.request.user.provider_profile
            if provider.provider_type == 'SELLER':
                return Seller.objects.filter(provider=provider)
        except Exception:
            pass
        return Seller.objects.none()
    
    def get_object(self):
        """Get seller profile for authenticated provider."""
        provider = self.request.user.provider_profile
        if provider.provider_type != 'SELLER':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a seller provider.')
        
        try:
            return provider.seller_profile
        except Seller.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Seller profile not found.')
    
    def perform_create(self, serializer):
        """Create seller profile for authenticated provider."""
        provider = self.request.user.provider_profile
        if provider.provider_type != 'SELLER':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a seller provider.')
        
        # Check if profile already exists
        if hasattr(provider, 'seller_profile'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Seller profile already exists.')
        
        serializer.save(provider=provider)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get seller provider status.
        
        GET /api/provider/seller/status/
        """
        try:
            provider = request.user.provider_profile
            if provider.provider_type != 'SELLER':
                return Response(
                    {'error': 'You are not a seller provider.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from providers.serializers.status import ProviderStatusSerializer
            return Response(ProviderStatusSerializer(provider).data)
        except Exception:
            return Response(
                {'error': 'Provider profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
