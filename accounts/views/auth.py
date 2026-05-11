"""
Authentication views for login and logout.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.authtoken.models import Token

from accounts.serializers.user import UserSerializer
from accounts.services import get_or_create_auth_token
from common.enums import UserRole


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login endpoint for all user types.
    
    POST /api/auth/login/
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "user": {
            "id": 1,
            "email": "user@example.com",
            "role": "PATIENT",
            "is_active": true,
            "created_at": "2026-01-26T10:00:00Z"
        },
        "token": "abc123..."
    }
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request, username=email.lower(), password=password)
    
    if user is None:
        # Try to get user to record failed attempt
        try:
            from accounts.models import User
            failed_user = User.objects.get(email__iexact=email.lower())
            failed_user.record_failed_login()
        except User.DoesNotExist:
            pass
        
        return Response(
            {'error': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Account is inactive.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check account status (separate from is_active)
    if not user.can_login:
        return Response(
            {
                'error': f'Account is {user.account_status.lower()}. Access denied.',
                'account_status': user.account_status
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # CRITICAL: Check provider approval status
    if user.role == UserRole.PROVIDER:
        try:
            from providers.models import Provider
            from common.enums import ProviderStatus
            provider = user.provider_profile
            
            if provider.status == ProviderStatus.PENDING:
                return Response(
                    {
                        'error': 'Account verification in progress.',
                        'provider_status': provider.status,
                        'message': 'Your account is currently being reviewed by our medical board. You will receive an email once your professional documents are verified.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            elif provider.status == ProviderStatus.REFUSED:
                return Response(
                    {
                        'error': 'Account registration refused.',
                        'provider_status': provider.status,
                        'refusal_reason': provider.refusal_reason,
                        'message': f'Your account registration was refused for the following reason: {provider.refusal_reason}. Please contact support or re-upload your documents.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            elif provider.status == ProviderStatus.SUSPENDED:
                return Response(
                    {
                        'error': 'Account suspended.',
                        'provider_status': provider.status,
                        'message': 'Your account has been temporarily suspended for administrative reasons. Please contact support.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            # Provider profile doesn't exist - allow login for now (edge case)
            pass
            
    # Check if account is locked (brute force protection)
    if user.is_locked():
        from django.utils import timezone as _tz
        remaining = user.locked_until - _tz.now()
        minutes_left = int(remaining.total_seconds() // 60) + 1
        return Response(
            {
                'error': 'Account temporarily locked due to multiple failed login attempts.',
                'message': f'Please try again in {minutes_left} minute{"s" if minutes_left != 1 else ""}.',
                'retry_after_minutes': minutes_left,
            },
            status=status.HTTP_423_LOCKED
        )
    
    # Record successful login (includes IP tracking and lock reset)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    user.record_login(ip_address=ip)
    
    token = get_or_create_auth_token(user)

    # Build base user payload
    user_data = UserSerializer(user).data

    # If this is a provider, enrich response with provider_type info
    if user.role == UserRole.PROVIDER:
        try:
            from providers.models import Provider
            provider = user.provider_profile
            # ProviderType is an enum; we expose both raw value and display
            from common.enums import ProviderType
            provider_type = provider.provider_type
            provider_type_display = ProviderType(provider_type).label if provider_type in ProviderType.values else provider.get_provider_type_display()

            user_data['provider_type'] = provider_type
            user_data['provider_type_display'] = provider_type_display
        except Exception:
            # If anything goes wrong, we still return a valid login response
            pass

    return Response({
        'user': user_data,
        'token': token.key,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint - deletes the authentication token.
    
    POST /api/auth/logout/
    
    Headers:
    Authorization: Token abc123...
    
    Response:
    {
        "message": "Successfully logged out."
    }
    """
    try:
        request.user.auth_token.delete()
    except Exception:
        pass  # Token might not exist
    
    return Response(
        {'message': 'Successfully logged out.'},
        status=status.HTTP_200_OK
    )
