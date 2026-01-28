"""
Django app configuration for notifications.
"""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Notifications'
    
    def ready(self):
        """Initialize signals and Firebase when the app is ready."""
        # Import signals to register them
        from . import signals  # noqa: F401
        
        # Initialize Firebase (optional - fails gracefully if not configured)
        try:
            from .services import FCMService
            FCMService.initialize()
        except Exception:
            pass
