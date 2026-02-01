"""Reports app configuration."""
from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """Configuration for the reports app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'
    verbose_name = 'Reports & Moderation'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            import reports.signals  # noqa: F401
        except ImportError:
            pass
