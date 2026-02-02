"""
Registration views for patients and providers.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.serializers.auth import (
    PatientRegisterSerializer,
    ProviderRegisterSerializer,
)
from accounts.services import (
    create_patient_user,
    create_provider_user,
    get_or_create_auth_token,
)
from accounts.serializers.user import UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def patient_register(request):
    """
    Register a new patient.
    
    POST /api/auth/patient/register/
    
    Request body:
    {
        "email": "patient@example.com",
        "password": "securepassword123",
        "password_confirm": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+213555123456"
    }
    
    Response:
    {
        "user": {
            "id": 1,
            "email": "patient@example.com",
            "role": "PATIENT",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+213555123456",
            "is_active": true,
            "created_at": "2026-01-26T10:00:00Z"
        },
        "token": "abc123..."
    }
    """
    serializer = PatientRegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = create_patient_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data['first_name'],
            last_name=serializer.validated_data['last_name'],
            phone_number=serializer.validated_data['phone_number'],
        )
        token = get_or_create_auth_token(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def provider_register(request):
    """
    Register a new provider.
    
    POST /api/auth/provider/register/
    
    Idempotent: If provider already exists, returns existing provider.
    If user exists with different role, returns 400 error.
    
    Request body:
    {
        "email": "doctor@example.com",
        "password": "securepassword123",
        "password_confirm": "securepassword123",
        "provider_type": "DOCTOR"
    }
    
    Response:
    {
        "user": {
            "id": 2,
            "email": "doctor@example.com",
            "role": "PROVIDER",
            "is_active": true,
            "created_at": "2026-01-26T10:00:00Z"
        },
        "provider": {
            "status": "PENDING",
            "refusal_reason": null,
            "verified_at": null
        },
        "token": "def456..."
    }
    """
    serializer = ProviderRegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            data = serializer.validated_data.copy()
            email = data.pop('email')
            password = data.pop('password')
            provider_type = data.pop('provider_type')
            data.pop('password_confirm', None) # Remove if present
            
            user, provider, is_new = create_provider_user(
                email=email,
                password=password,
                provider_type=provider_type,
                **data
            )
            token = get_or_create_auth_token(user)
            
            from providers.serializers.status import ProviderStatusSerializer
            
            # Return 200 if provider already existed (idempotent), 201 if new
            http_status = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
            
            return Response({
                'user': UserSerializer(user).data,
                'provider': ProviderStatusSerializer(provider).data,
                'token': token.key,
            }, status=http_status)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
