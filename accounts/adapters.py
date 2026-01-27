"""
Custom account adapter for django-allauth API usage.
"""
from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter to disable email verification for API usage.
    In production, you may want to enable email verification.
    """
    def is_open_for_signup(self, request):
        """Allow signup without email verification for API."""
        return True
    
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """Override to disable email confirmation for API."""
        # Skip email confirmation for API usage
        # Uncomment below to enable email verification:
        # return super().send_confirmation_mail(request, emailconfirmation, signup)
        pass
