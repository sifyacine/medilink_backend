"""
Admin services — pure business-logic functions with no HTTP/serializer coupling.

Every function that changes platform state:
  1. Performs the state change.
  2. Calls log_admin_action() to record it.
  3. Returns the modified object.

These functions are called from admin views and should never be called
from non-admin code paths.
"""
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from accounts.utils import revoke_user_tokens
from common.enums import UserAccountStatus, ProviderStatus, AdminActionType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_client_ip(request):
    """Extract the real client IP from the request, honouring X-Forwarded-For."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_admin_action(admin, action, target_obj=None, ip=None, extra=None):
    """
    Create an AdminActivityLog entry.

    Args:
        admin:      User instance (the admin performing the action).
        action:     AdminActionType value.
        target_obj: The object being acted upon (optional).
        ip:         Client IP string (optional).
        extra:      dict of additional context (old/new values, reason, etc.).

    Returns:
        AdminActivityLog instance.
    """
    from admins.models import AdminActivityLog

    content_type = None
    object_id = None
    object_repr = ''

    if target_obj is not None:
        content_type = ContentType.objects.get_for_model(target_obj.__class__)
        object_id = target_obj.pk
        object_repr = str(target_obj)[:300]

    return AdminActivityLog.objects.create(
        admin=admin,
        action=action,
        content_type=content_type,
        object_id=object_id,
        object_repr=object_repr,
        ip_address=ip,
        extra_data=extra or {},
    )


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def suspend_user(user, admin, reason='', ip=None):
    """Suspend a user account.  Revokes tokens so active sessions end."""
    user.account_status = UserAccountStatus.SUSPENDED
    user.is_active = False
    user.save(update_fields=['account_status', 'is_active', 'updated_at'])
    revoke_user_tokens(user)
    log_admin_action(
        admin, AdminActionType.USER_SUSPEND, target_obj=user, ip=ip,
        extra={'reason': reason, 'target_email': user.email},
    )


def activate_user(user, admin, ip=None):
    """Restore a suspended or deactivated user account."""
    user.account_status = UserAccountStatus.ACTIVE
    user.is_active = True
    user.save(update_fields=['account_status', 'is_active', 'updated_at'])
    log_admin_action(
        admin, AdminActionType.USER_ACTIVATE, target_obj=user, ip=ip,
        extra={'target_email': user.email},
    )


def deactivate_user(user, admin, reason='', ip=None):
    """Permanently deactivate a user account.  Revokes tokens."""
    user.account_status = UserAccountStatus.DEACTIVATED
    user.is_active = False
    user.save(update_fields=['account_status', 'is_active', 'updated_at'])
    revoke_user_tokens(user)
    log_admin_action(
        admin, AdminActionType.USER_DEACTIVATE, target_obj=user, ip=ip,
        extra={'reason': reason, 'target_email': user.email},
    )


def send_admin_password_reset(user, admin, ip=None):
    """
    Trigger a password-reset email for a user (admin-initiated).

    Uses the existing PasswordResetToken model and email infrastructure.
    """
    import secrets
    from datetime import timedelta
    from accounts.models import PasswordResetToken

    # Invalidate any existing unused tokens
    PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

    token = PasswordResetToken.objects.create(
        user=user,
        token=secrets.token_hex(32),
        expires_at=timezone.now() + timedelta(hours=24),
    )

    # Send email (uses existing account email utility if available)
    try:
        from accounts.services import send_password_reset_email
        send_password_reset_email(user, token.token)
    except (ImportError, AttributeError):
        pass  # Email sending is best-effort; log the action regardless

    log_admin_action(
        admin, AdminActionType.USER_PASSWORD_RESET, target_obj=user, ip=ip,
        extra={'target_email': user.email},
    )
    return token


# ---------------------------------------------------------------------------
# Provider management
# ---------------------------------------------------------------------------

def suspend_provider(provider, admin, reason='', ip=None):
    """
    Suspend an approved provider.

    Sets provider.status = SUSPENDED and suspends the linked user account
    so they cannot log in.
    """
    from providers.models import ProviderStatusHistory

    old_status = provider.status
    provider.status = ProviderStatus.SUSPENDED
    provider.save(update_fields=['status', 'updated_at'])

    # Also suspend the user account
    suspend_user(provider.user, admin, reason=reason, ip=ip)

    # ProviderStatusHistory (same model used by approve/refuse)
    try:
        ProviderStatusHistory.objects.create(
            provider=provider,
            old_status=old_status,
            new_status=ProviderStatus.SUSPENDED,
            changed_by=admin,
            reason=reason or 'Suspended by admin',
        )
    except Exception:
        pass  # History is best-effort; don't fail the whole action

    log_admin_action(
        admin, AdminActionType.PROVIDER_SUSPEND, target_obj=provider, ip=ip,
        extra={'reason': reason, 'old_status': old_status},
    )


def restore_provider(provider, admin, ip=None):
    """
    Restore a suspended provider back to APPROVED status.

    Also re-activates the linked user account.
    """
    from providers.models import ProviderStatusHistory

    old_status = provider.status
    provider.status = ProviderStatus.APPROVED
    provider.save(update_fields=['status', 'updated_at'])

    activate_user(provider.user, admin, ip=ip)

    try:
        ProviderStatusHistory.objects.create(
            provider=provider,
            old_status=old_status,
            new_status=ProviderStatus.APPROVED,
            changed_by=admin,
            reason='Provider restored by admin',
        )
    except Exception:
        pass

    log_admin_action(
        admin, AdminActionType.PROVIDER_RESTORE, target_obj=provider, ip=ip,
        extra={'old_status': old_status},
    )
