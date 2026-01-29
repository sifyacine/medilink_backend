"""
Prescriptions app configuration.
"""
from django.apps import AppConfig


class PrescriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prescriptions'
    verbose_name = 'Prescriptions'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            from . import signals  # noqa
        except ImportError:
            pass
