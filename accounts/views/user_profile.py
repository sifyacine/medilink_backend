"""
User profile management views for GET /me/ and PATCH /me/ endpoints.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.serializers.profile import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def get_my_profile(request):
    """
    Get or update comprehensive profile of authenticated user.
    
    GET /api/auth/me/ - Get full profile
    PATCH /api/auth/me/ - Update profile (safe fields only)
    
    Returns aggregated profile data including:
    - Basic user information
    - Role-specific profile data (provider/patient)
    - Verification status
    - Profile completion metrics
    
    Headers:
    Authorization: Token abc123...
    
    GET Response:
    {
        "id": 1,
        "email": "user@example.com",
        "role": "PROVIDER",
        "account_status": "ACTIVE",
        "email_verified": true,
        "profile_completed": true,
        "profile_completion_percentage": 85,
        "provider_profile": {
            "status": "APPROVED",
            "provider_type": "DOCTOR",
            "doctor": { ... }
        },
        ...
    }
    
    PATCH Request body:
    {
        // Only safe fields can be updated
        // Role-specific updates should use dedicated endpoints
    }
    """
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            # Return full profile after update
            profile_serializer = UserProfileSerializer(request.user)
            return Response(profile_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


