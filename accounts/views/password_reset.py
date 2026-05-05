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

_RESET_EMAIL_SUBJECT = "Reset your MediLink password"

_RESET_EMAIL_TEXT = """Hello {name},

We received a request to reset the password for your MediLink account.

Click the link below to choose a new password:
{reset_link}

This link expires in 24 hours. If you did not request a password reset, you can safely ignore this email.

— The MediLink Team
"""

_RESET_EMAIL_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:8px;overflow:hidden;
                    box-shadow:0 2px 8px rgba(0,0,0,.08);">
        <tr>
          <td style="background:#1a6fb5;padding:24px 32px;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;">MediLink</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <p style="margin:0 0 16px;font-size:16px;color:#333;">Hello {name},</p>
            <p style="margin:0 0 24px;font-size:15px;color:#555;line-height:1.6;">
              We received a request to reset the password for your MediLink account.
              Click the button below to choose a new password.
            </p>
            <p style="text-align:center;margin:0 0 24px;">
              <a href="{reset_link}"
                 style="display:inline-block;background:#1a6fb5;color:#ffffff;
                        text-decoration:none;padding:14px 32px;border-radius:6px;
                        font-size:15px;font-weight:bold;">
                Reset Password
              </a>
            </p>
            <p style="margin:0 0 8px;font-size:13px;color:#888;">
              Or copy this link into your browser:
            </p>
            <p style="margin:0 0 24px;font-size:13px;color:#1a6fb5;word-break:break-all;">
              {reset_link}
            </p>
            <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
            <p style="margin:0;font-size:13px;color:#aaa;">
              This link expires in <strong>24 hours</strong>. If you did not request a
              password reset, you can safely ignore this email.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f9f9f9;padding:16px 32px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#bbb;">
              &copy; 2025 MediLink. All rights reserved.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Request a password reset email.

    POST /api/auth/password/reset/
    {
        "email": "user@example.com"
    }

    Always returns HTTP 200 regardless of whether the email exists (prevents
    email enumeration).
    """
    email = request.data.get('email')

    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email__iexact=email.strip().lower())

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://dzmedilink.netlify.app')
        reset_link = f"{frontend_url}/reset-password/{uid}/{token}/"

        name = user.get_full_name() or user.email
        send_mail(
            subject=_RESET_EMAIL_SUBJECT,
            message=_RESET_EMAIL_TEXT.format(name=name, reset_link=reset_link),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=_RESET_EMAIL_HTML.format(name=name, reset_link=reset_link),
            fail_silently=False,
        )

    except User.DoesNotExist:
        pass  # Same response — do not reveal whether email exists

    return Response(
        {'message': 'If an account with that email exists, a reset link has been sent.'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirm password reset with token.

    POST /api/auth/password/reset/confirm/
    {
        "uid": "<base64_encoded_user_id>",
        "token": "<reset_token>",
        "new_password": "newpassword123",
        "new_password_confirm": "newpassword123"
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
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)

        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired reset token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        # Revoke all existing auth tokens so old sessions cannot be reused
        from rest_framework.authtoken.models import Token
        Token.objects.filter(user=user).delete()

        return Response(
            {'message': 'Password reset successfully.'},
            status=status.HTTP_200_OK
        )

    except (User.DoesNotExist, ValueError, TypeError):
        return Response(
            {'error': 'Invalid reset token.'},
            status=status.HTTP_400_BAD_REQUEST
        )
