"""
Invoices app configuration.
"""
from django.apps import AppConfig


class InvoicesConfig(AppConfig):
    """Configuration for the invoices app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoices'
    verbose_name = 'Invoices'
    
    def ready(self):
        """Import signals when app is ready."""
        import invoices.signals  # noqa: F401
