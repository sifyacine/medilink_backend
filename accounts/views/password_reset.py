"""
Password reset views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Request password reset.
    
    POST /api/auth/password/reset/
    
    Request body:
    {
        "email": "user@example.com"
    }
    
    Response:
    {
        "message": "Password reset email sent if account exists."
    }
    
    Note: Always returns success message (security best practice)
    """
    email = request.data.get('email')
    
    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email__iexact=email.lower())
        
        # Generate reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # In production, send email with reset link
        # For now, return token in response (development only)
        reset_link = f"{settings.FRONTEND_URL or 'http://localhost:3000'}/reset-password/{uid}/{token}/"
        
        # TODO: Send email in production
        # send_mail(
        #     subject='Password Reset Request',
        #     message=f'Reset your password: {reset_link}',
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[user.email],
        # )
        
        return Response({
            'message': 'Password reset email sent if account exists.',
            # Remove in production:
            'reset_link': reset_link if settings.DEBUG else None,
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        # Return same message for security (don't reveal if email exists)
        return Response({
            'message': 'Password reset email sent if account exists.'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirm password reset with token.
    
    POST /api/auth/password/reset/confirm/
    
    Request body:
    {
        "uid": "base64_encoded_user_id",
        "token": "reset_token",
        "new_password": "newpassword123",
        "new_password_confirm": "newpassword123"
    }
    
    Response:
    {
        "message": "Password reset successfully."
    }
    """
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    new_password_confirm = request.data.get('new_password_confirm')
    
    if not all([uid, token, new_password, new_password_confirm]):
        return Response(
            {'error': 'All fields are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password != new_password_confirm:
        return Response(
            {'error': 'Passwords do not match.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Decode user ID
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        # Verify token
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired reset token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Revoke all existing tokens (security)
        from rest_framework.authtoken.models import Token
        Token.objects.filter(user=user).delete()
        
        return Response({
            'message': 'Password reset successfully.'
        }, status=status.HTTP_200_OK)
        
    except (User.DoesNotExist, ValueError, TypeError):
        return Response(
            {'error': 'Invalid reset token.'},
            status=status.HTTP_400_BAD_REQUEST
        )
