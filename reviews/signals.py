"""
Signals for the reviews app.
Automatically updates review aggregates when reviews change.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from reviews.models import Review, ReviewAggregate, ReviewHelpful


@receiver(post_save, sender=Review)
def update_review_aggregate_on_save(sender, instance, **kwargs):
    """Update aggregate statistics when a review is saved."""
    ReviewAggregate.update_for_object(
        content_type=instance.reviewed_content_type,
        object_id=instance.reviewed_object_id
    )
    transaction.on_commit(lambda: _push_dashboard_review_update(instance))


@receiver(post_delete, sender=Review)
def update_review_aggregate_on_delete(sender, instance, **kwargs):
    """Update aggregate statistics when a review is deleted."""
    ReviewAggregate.update_for_object(
        content_type=instance.reviewed_content_type,
        object_id=instance.reviewed_object_id
    )
    transaction.on_commit(lambda: _push_dashboard_review_update(instance))


@receiver(post_save, sender=ReviewHelpful)
def update_helpful_count_on_save(sender, instance, created, **kwargs):
    """Update helpful count when a vote is added."""
    if created:
        review = instance.review
        review.helpful_count = review.helpful_votes.count()
        review.save(update_fields=['helpful_count'])


@receiver(post_delete, sender=ReviewHelpful)
def update_helpful_count_on_delete(sender, instance, **kwargs):
    """Update helpful count when a vote is removed."""
    try:
        review = instance.review
        review.helpful_count = review.helpful_votes.count()
        review.save(update_fields=['helpful_count'])
    except Review.DoesNotExist:
        pass  # Review was deleted, no need to update


# ------------------------------------------------------------------
# Dashboard push helper
# ------------------------------------------------------------------

def _push_dashboard_review_update(review_instance):
    """Resolve the reviewed provider and push updated review stats."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        from django.contrib.contenttypes.models import ContentType
        from providers.models.provider import Provider

        ct = review_instance.reviewed_content_type
        # Only push if the reviewed object is a Provider
        provider_ct = ContentType.objects.get_for_model(Provider)
        if ct.pk != provider_ct.pk:
            return

        provider = Provider.objects.select_related('user').get(
            pk=review_instance.reviewed_object_id
        )

        from notifications.services import WebSocketBroadcaster
        from notifications.dashboard_services import DashboardStatsService

        data = DashboardStatsService.get_review_stats(provider)
        WebSocketBroadcaster.send_to_dashboard(
            user_id=provider.user_id,
            message_type='dashboard_reviews_updated',
            data=data,
        )
    except Exception as e:
        logger.error("Error pushing dashboard review update: %s", e)
