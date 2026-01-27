from django.apps import AppConfig


class MedicalRecordConfig(AppConfig):
    name = 'medical_record'
    
    def ready(self):
        """Import signals when app is ready."""
        import medical_record.signals  # noqa
