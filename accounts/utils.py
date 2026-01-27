"""
Utility functions for account management.
"""
from rest_framework.authtoken.models import Token


def revoke_user_tokens(user):
    """
    Revoke all authentication tokens for a user.
    
    This should be called when:
    - Account status changes (suspended/deactivated)
    - Provider status changes (verified/refused)
    - Role changes
    - Security incidents
    
    Args:
        user: User instance
    """
    try:
        Token.objects.filter(user=user).delete()
    except Exception:
        pass  # Token might not exist


def revoke_tokens_on_status_change(sender, instance, **kwargs):
    """
    Signal handler to revoke tokens when provider status changes.
    
    This ensures that when a provider is refused or status changes,
    their existing tokens become invalid.
    """
    if hasattr(instance, 'user'):
        revoke_user_tokens(instance.user)
