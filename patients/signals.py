from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from patients.models import ProviderPatientAccess


@receiver(post_save, sender=ProviderPatientAccess)
def push_dashboard_on_patient_access_save(sender, instance, **kwargs):
    provider = instance.provider
    transaction.on_commit(lambda: _push_dashboard_patient_update(provider))


@receiver(post_delete, sender=ProviderPatientAccess)
def push_dashboard_on_patient_access_delete(sender, instance, **kwargs):
    provider = instance.provider
    transaction.on_commit(lambda: _push_dashboard_patient_update(provider))


def _push_dashboard_patient_update(provider):
    try:
        from notifications.dashboard_services import DashboardStatsService
        from notifications.services import WebSocketBroadcaster

        stats = DashboardStatsService.get_patient_stats(provider)
        WebSocketBroadcaster.send_to_dashboard(
            user_id=provider.user_id,
            message_type="dashboard_patients_updated",
            data={"patients": stats},
        )
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "Failed to push dashboard patient update for provider %s", provider.id
        )
