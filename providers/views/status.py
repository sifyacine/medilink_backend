"""
Provider status views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from providers.models.provider import Provider
from providers.serializers.status import ProviderStatusSerializer
from common.permissions import IsProvider, IsOwnerOrAdmin


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProvider])
def provider_status(request):
    """
    Get provider status information.
    
    GET /api/provider/status/
    
    Headers:
    Authorization: Token abc123...
    
    Response:
    {
        "status": "PENDING",
        "refusal_reason": null,
        "verified_at": null
    }
    
    Or if refused:
    {
        "status": "REFUSED",
        "refusal_reason": "Incomplete documentation",
        "verified_at": null
    }
    """
    try:
        provider = request.user.provider_profile
    except Provider.DoesNotExist:
        return Response(
            {'error': 'Provider profile not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = ProviderStatusSerializer(provider)
    return Response(serializer.data, status=status.HTTP_200_OK)
