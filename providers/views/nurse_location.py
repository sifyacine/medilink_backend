"""
Nurse location tracking views.
Handles real-time location updates for nurses.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from providers.models.nurse import Nurse, NurseLocation
from providers.serializers.nurse import NurseLocationSerializer
from common.permissions import IsNurse


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated, IsNurse])
def nurse_location(request):
    """
    Get, create, or update nurse's current location.

    GET /api/nurse/location/ - Get current location
    POST /api/nurse/location/ - Create location (first time)
    PUT /api/nurse/location/ - Update location

    Request body (POST/PUT):
    {
        "latitude": "36.7372",
        "longitude": "3.0869",
        "accuracy_meters": 15,  # optional
        "is_active": true
    }
    """
    try:
        nurse = request.user.provider_profile.nurse_profile
    except (AttributeError, Nurse.DoesNotExist):
        return Response(
            {'error': 'Nurse profile not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        try:
            location = nurse.current_location
            serializer = NurseLocationSerializer(location)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except NurseLocation.DoesNotExist:
            return Response(
                {'error': 'Location not found. Please submit your location first.'},
                status=status.HTTP_404_NOT_FOUND
            )

    elif request.method in ['POST', 'PUT']:
        try:
            location = nurse.current_location
            # Existing location - update it
            serializer = NurseLocationSerializer(location, data=request.data, partial=True)
        except NurseLocation.DoesNotExist:
            # First time - create new location
            data = request.data.copy()
            data['nurse'] = nurse.id
            serializer = NurseLocationSerializer(data=data)

        if serializer.is_valid():
            if request.method == 'POST':
                # Ensure nurse reference is set
                serializer.validated_data['nurse'] = nurse
            serializer.save(nurse=nurse)
            return Response(serializer.data, status=status.HTTP_201_CREATED if request.method == 'POST' else status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsNurse])
def nurse_location_toggle(request):
    """
    Toggle location tracking on/off for nurse.

    PATCH /api/nurse/location/toggle/

    Request body:
    {
        "is_active": false
    }
    """
    try:
        nurse = request.user.provider_profile.nurse_profile
    except (AttributeError, Nurse.DoesNotExist):
        return Response(
            {'error': 'Nurse profile not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        location = nurse.current_location
    except NurseLocation.DoesNotExist:
        return Response(
            {'error': 'Location not found. Please submit your location first.'},
            status=status.HTTP_404_NOT_FOUND
        )

    is_active = request.data.get('is_active')
    if is_active is None:
        return Response(
            {'error': 'is_active field is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    location.is_active = is_active
    location.save()

    serializer = NurseLocationSerializer(location)
    return Response(serializer.data, status=status.HTTP_200_OK)
