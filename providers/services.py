"""
Business logic services for providers.
"""
from django.utils import timezone

from providers.models import Provider, ProviderStatusHistory
from common.enums import ProviderStatus
from accounts.utils import revoke_user_tokens


def approve_provider(provider, approved_by):
    """
    Approve a provider and create status history entry.
    
    Args:
        provider: Provider instance
        approved_by: User instance (admin)
        
    Returns:
        Provider instance
    """
    old_status = provider.status
    provider.approve(approved_by)
    
    # Create status history entry
    ProviderStatusHistory.objects.create(
        provider=provider,
        old_status=old_status,
        new_status=ProviderStatus.APPROVED,
        changed_by=approved_by,
        reason='Provider approved by admin',
    )
    
    # Revoke existing tokens - user needs to re-authenticate after approval
    revoke_user_tokens(provider.user)
    
    return provider


def verify_provider(provider, verified_by):
    """Legacy function - use approve_provider() instead."""
    return approve_provider(provider, verified_by)


def refuse_provider(provider, reason, refused_by):
    """
    Refuse a provider and create status history entry.
    
    Args:
        provider: Provider instance
        reason: Reason for refusal (string)
        refused_by: User instance (admin)
        
    Returns:
        Provider instance
        
    Raises:
        ValueError: If reason is empty
    """
    if not reason or not reason.strip():
        raise ValueError('Refusal reason is required')
    
    old_status = provider.status
    provider.refuse(reason, refused_by)
    
    # Create status history entry
    ProviderStatusHistory.objects.create(
        provider=provider,
        old_status=old_status,
        new_status=ProviderStatus.REFUSED,
        changed_by=refused_by,
        reason=reason,
    )
    
    # Revoke tokens when provider is refused
    revoke_user_tokens(provider.user)
    
    return provider
