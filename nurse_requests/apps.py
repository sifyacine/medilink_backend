from django.apps import AppConfig


class NurseRequestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nurse_requests'
    verbose_name = 'On-Demand Nursing Services'

    def ready(self):
        import nurse_requests.signals  # noqa
