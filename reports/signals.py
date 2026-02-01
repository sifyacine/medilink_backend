"""
Signals for the reports app.
Automatically updates report aggregates when reports change.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from reports.models import Report, ReportAggregate


@receiver(post_save, sender=Report)
def update_report_aggregate_on_save(sender, instance, **kwargs):
    """Update aggregate statistics when a report is saved."""
    ReportAggregate.update_for_object(
        content_type=instance.reported_content_type,
        object_id=instance.reported_object_id
    )


@receiver(post_delete, sender=Report)
def update_report_aggregate_on_delete(sender, instance, **kwargs):
    """Update aggregate statistics when a report is deleted."""
    ReportAggregate.update_for_object(
        content_type=instance.reported_content_type,
        object_id=instance.reported_object_id
    )
