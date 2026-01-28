"""
Django app configuration for appointments.
"""
from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appointments'
    verbose_name = 'Appointments'
    
    def ready(self):
        import appointments.signals  # noqa
