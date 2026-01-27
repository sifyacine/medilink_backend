"""
Custom authentication classes with built-in access guards.
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from accounts.models import User
from common.enums import UserAccountStatus, UserRole
from providers.models import Provider
from common.enums import ProviderStatus


class TokenAuthenticationWithAccountStatus(TokenAuthentication):
    """
    Token authentication that enforces account status checks.
    
    This ensures that:
    - Suspended/deactivated users cannot authenticate
    - Pending/refused providers cannot access protected resources
    """
    
    def authenticate_credentials(self, key):
        """
        Authenticate token and check account status.
        
        Raises AuthenticationFailed if:
        - Token is invalid
        - Account is suspended or deactivated
        - Provider is not verified (for provider routes)
        """
        user, token = super().authenticate_credentials(key)
        
        # Check account status
        if not user.can_login:
            raise AuthenticationFailed(
                f'Account is {user.account_status.lower()}. Access denied.'
            )
        
        return user, token


class ProviderTokenAuthentication(TokenAuthenticationWithAccountStatus):
    """
    Token authentication specifically for provider routes.
    
    Enforces that:
    1. User must be authenticated
    2. User must have PROVIDER role
    3. Provider must be VERIFIED
    
    This is the centralized guard that prevents PENDING/REFUSED providers
    from accessing protected provider resources.
    """
    
    def authenticate_credentials(self, key):
        """
        Authenticate and verify provider status.
        
        Raises AuthenticationFailed if provider is not verified.
        """
        user, token = super().authenticate_credentials(key)
        
        # Check if user is a provider
        if user.role != UserRole.PROVIDER:
            raise AuthenticationFailed('User is not a provider.')
        
        # Check provider approval status
        try:
            provider = user.provider_profile
            if provider.status != ProviderStatus.APPROVED:
                if provider.status == ProviderStatus.PENDING:
                    raise AuthenticationFailed(
                        'Provider account is pending approval. '
                        'Please wait for admin approval before accessing this resource.'
                    )
                elif provider.status == ProviderStatus.REFUSED:
                    raise AuthenticationFailed(
                        f'Provider account has been refused. '
                        f'Reason: {provider.refusal_reason or "No reason provided"}.'
                    )
                else:
                    raise AuthenticationFailed(
                        f'Provider account is {provider.status.lower()}. '
                        'Approval required to access this resource.'
                    )
        except Provider.DoesNotExist:
            raise AuthenticationFailed('Provider profile not found.')
        
        return user, token
