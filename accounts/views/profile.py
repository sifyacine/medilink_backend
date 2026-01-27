"""
User profile self-management views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.serializers.profile import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)
from accounts.models import User
from common.enums import UserRole


@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def get_my_profile(request):
    """
    Get or update current user's complete profile information.
    
    GET /api/auth/me/ - Get profile
    PATCH /api/auth/me/ - Update profile (safe fields only)
    PUT /api/auth/me/ - Update profile (safe fields only)
    
    Returns aggregated profile data including:
    - User account information
    - Provider profile (if user is a provider)
    - Role-specific data
    
    Headers:
    Authorization: Token abc123...
    
    GET Response:
    {
        "id": 1,
        "email": "user@example.com",
        "role": "PROVIDER",
        "role_display": "Provider",
        "account_status": "ACTIVE",
        "account_status_display": "Active",
        "is_active": true,
        "email_verified": false,
        "profile_completion_percentage": 45,
        "last_login": "2026-01-26T10:00:00Z",
        "created_at": "2026-01-25T10:00:00Z",
        "provider_profile": {
            "status": "PENDING",
            "refusal_reason": null,
            "verified_at": null
        }
    }
    
    PATCH Request Body:
    {
        "profile_completion_percentage": 75
    }
    """
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # PATCH or PUT
    serializer = UserProfileUpdateSerializer(
        request.user,
        data=request.data,
        partial=True,
        context={"request": request},
    )
    
    if serializer.is_valid():
        serializer.save()
        
        # Return full profile after update
        full_serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response(full_serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
