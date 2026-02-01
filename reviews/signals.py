"""
Signals for the reviews app.
Automatically updates review aggregates when reviews change.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from reviews.models import Review, ReviewAggregate, ReviewHelpful


@receiver(post_save, sender=Review)
def update_review_aggregate_on_save(sender, instance, **kwargs):
    """Update aggregate statistics when a review is saved."""
    ReviewAggregate.update_for_object(
        content_type=instance.reviewed_content_type,
        object_id=instance.reviewed_object_id
    )


@receiver(post_delete, sender=Review)
def update_review_aggregate_on_delete(sender, instance, **kwargs):
    """Update aggregate statistics when a review is deleted."""
    ReviewAggregate.update_for_object(
        content_type=instance.reviewed_content_type,
        object_id=instance.reviewed_object_id
    )


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
