"""
Generic Reviews & Ratings system for the Medilink platform.

This module provides a fully generic, reusable review system that supports:
- Anyone can review anything (Patient → Nurse, Nurse → Patient, etc.)
- Rating (1-5 stars)
- Text review with optional image
- Generic Foreign Key for reviewed object
- Duplicate prevention per reviewer/target/context
- Aggregate ratings (average, count) via ReviewableModel mixin

Usage examples:
- Patient reviews Nurse after service
- Nurse reviews Patient
- Patient reviews Doctor after appointment
- Patient reviews Clinic
- Patient reviews Product
- Future: Any entity reviewing any other entity

Architecture decisions:
1. Uses Django's ContentType framework for polymorphic relationships
2. Supports optional "context" (e.g., appointment, service request) to prevent duplicates
3. Provides a ReviewableModel mixin for easy integration with existing models
4. Review aggregates are cached on the reviewed object for performance
"""
import uuid
from django.db import models
from django.db.models import Avg, Count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.exceptions import ValidationError

from accounts.models import User


class ReviewStatus(models.TextChoices):
    """Review status choices."""
    ACTIVE = 'ACTIVE', 'Active'
    HIDDEN = 'HIDDEN', 'Hidden by Admin'
    DELETED = 'DELETED', 'Deleted by User'
    FLAGGED = 'FLAGGED', 'Flagged for Review'


class Review(models.Model):
    """
    Generic Review model that can be attached to any reviewable entity.
    
    Supports:
    - Any user can leave reviews for any model instance
    - Each review has a rating (1-5), optional text, and optional image
    - Context tracking to prevent duplicate reviews for same service/appointment
    - Soft delete support
    - Moderation status
    
    Relationships:
    - reviewer: The user leaving the review
    - reviewed_object: Any model instance (via GenericForeignKey)
    - context_object: Optional context (e.g., appointment, service request)
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Reviewer (required)
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given',
        help_text='User who wrote this review'
    )
    
    # Reviewed entity (Generic Foreign Key)
    reviewed_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='reviews_for',
        help_text='Content type of the reviewed object'
    )
    reviewed_object_id = models.CharField(
        max_length=255,
        help_text='ID of the reviewed object (supports UUID and int)'
    )
    reviewed_object = GenericForeignKey(
        'reviewed_content_type',
        'reviewed_object_id'
    )
    
    # Context for the review (e.g., appointment, nurse service request)
    # Prevents duplicate reviews for the same context
    context_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_contexts',
        help_text='Content type of the context object'
    )
    context_object_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='ID of the context object'
    )
    context_object = GenericForeignKey(
        'context_content_type',
        'context_object_id'
    )
    
    # Review content
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5 stars'
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text='Optional review title'
    )
    text = models.TextField(
        blank=True,
        help_text='Review text content'
    )
    image = models.ImageField(
        upload_to='reviews/images/',
        null=True,
        blank=True,
        help_text='Optional review image'
    )
    
    # Status and moderation
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.ACTIVE,
        db_index=True,
        help_text='Review status'
    )
    
    # Response from reviewed entity (optional)
    response = models.TextField(
        blank=True,
        help_text='Response from the reviewed entity'
    )
    response_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the response was added'
    )
    response_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_responses',
        help_text='User who responded to this review'
    )
    
    # Helpful votes
    helpful_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of helpful votes'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the review was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reviewed_content_type', 'reviewed_object_id']),
            models.Index(fields=['reviewer', 'status']),
            models.Index(fields=['context_content_type', 'context_object_id']),
            models.Index(fields=['rating']),
            models.Index(fields=['status', '-created_at']),
        ]
        constraints = [
            # Prevent duplicate reviews for the same context
            models.UniqueConstraint(
                fields=[
                    'reviewer',
                    'reviewed_content_type',
                    'reviewed_object_id',
                    'context_content_type',
                    'context_object_id'
                ],
                name='unique_review_with_context',
                condition=models.Q(context_content_type__isnull=False)
            ),
            # Prevent duplicate reviews without context (only one review per reviewer/target)
            models.UniqueConstraint(
                fields=[
                    'reviewer',
                    'reviewed_content_type',
                    'reviewed_object_id'
                ],
                name='unique_review_without_context',
                condition=models.Q(context_content_type__isnull=True)
            ),
        ]
    
    def __str__(self):
        return f'Review by {self.reviewer.email} - {self.rating}★'
    
    def clean(self):
        """Validate the review."""
        super().clean()
        
        # Validate rating range
        if self.rating < 1 or self.rating > 5:
            raise ValidationError({
                'rating': 'Rating must be between 1 and 5.'
            })
        
        # Prevent self-review
        if self.reviewer_id and self.reviewed_content_type_id:
            if (self.reviewed_content_type.model_class() == User and
                    str(self.reviewed_object_id) == str(self.reviewer_id)):
                raise ValidationError('Users cannot review themselves.')
    
    def add_response(self, response_text, response_by, save=True):
        """Add a response to this review."""
        self.response = response_text
        self.response_at = timezone.now()
        self.response_by = response_by
        
        if save:
            self.save(update_fields=['response', 'response_at', 'response_by', 'updated_at'])
    
    def hide(self, save=True):
        """Hide the review (admin moderation)."""
        self.status = ReviewStatus.HIDDEN
        if save:
            self.save(update_fields=['status', 'updated_at'])
    
    def flag(self, save=True):
        """Flag the review for moderation."""
        self.status = ReviewStatus.FLAGGED
        if save:
            self.save(update_fields=['status', 'updated_at'])
    
    def soft_delete(self, save=True):
        """Soft delete the review."""
        self.status = ReviewStatus.DELETED
        if save:
            self.save(update_fields=['status', 'updated_at'])


class ReviewHelpful(models.Model):
    """
    Track helpful votes for reviews.
    Prevents users from voting multiple times.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpful_votes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='helpful_votes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_helpful_votes'
        verbose_name = 'Review Helpful Vote'
        verbose_name_plural = 'Review Helpful Votes'
        unique_together = [['review', 'user']]
    
    def __str__(self):
        return f'{self.user.email} found review {self.review_id} helpful'


class ReviewAggregate(models.Model):
    """
    Cached aggregate statistics for reviewed entities.
    Updated automatically when reviews change.
    
    This table stores pre-computed aggregates for performance,
    avoiding expensive COUNT/AVG queries on every page load.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Reviewed entity (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='review_aggregates'
    )
    object_id = models.CharField(
        max_length=255,
        help_text='ID of the reviewed object'
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Aggregate data
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text='Average rating (1.00 - 5.00)'
    )
    review_count = models.PositiveIntegerField(
        default=0,
        help_text='Total number of active reviews'
    )
    
    # Rating distribution
    rating_1_count = models.PositiveIntegerField(default=0)
    rating_2_count = models.PositiveIntegerField(default=0)
    rating_3_count = models.PositiveIntegerField(default=0)
    rating_4_count = models.PositiveIntegerField(default=0)
    rating_5_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'review_aggregates'
        verbose_name = 'Review Aggregate'
        verbose_name_plural = 'Review Aggregates'
        unique_together = [['content_type', 'object_id']]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['average_rating']),
        ]
    
    def __str__(self):
        return f'{self.content_type.model}: {self.object_id} - {self.average_rating}★ ({self.review_count} reviews)'
    
    @classmethod
    def update_for_object(cls, content_type, object_id):
        """
        Update aggregate statistics for a specific object.
        Called automatically via signals when reviews change.
        """
        from django.db.models import Avg, Count, Q
        
        # Get active reviews for this object
        reviews = Review.objects.filter(
            reviewed_content_type=content_type,
            reviewed_object_id=str(object_id),
            status=ReviewStatus.ACTIVE
        )
        
        # Calculate aggregates
        stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            total_count=Count('id'),
            r1=Count('id', filter=Q(rating=1)),
            r2=Count('id', filter=Q(rating=2)),
            r3=Count('id', filter=Q(rating=3)),
            r4=Count('id', filter=Q(rating=4)),
            r5=Count('id', filter=Q(rating=5)),
        )
        
        # Update or create aggregate record
        aggregate, _ = cls.objects.update_or_create(
            content_type=content_type,
            object_id=str(object_id),
            defaults={
                'average_rating': stats['avg_rating'] or 0,
                'review_count': stats['total_count'] or 0,
                'rating_1_count': stats['r1'] or 0,
                'rating_2_count': stats['r2'] or 0,
                'rating_3_count': stats['r3'] or 0,
                'rating_4_count': stats['r4'] or 0,
                'rating_5_count': stats['r5'] or 0,
            }
        )
        
        return aggregate


def get_reviews_for_object(obj):
    """
    Utility function to get all active reviews for any model instance.
    
    Usage:
        reviews = get_reviews_for_object(nurse_instance)
        reviews = get_reviews_for_object(doctor_instance)
    """
    content_type = ContentType.objects.get_for_model(obj)
    return Review.objects.filter(
        reviewed_content_type=content_type,
        reviewed_object_id=str(obj.pk),
        status=ReviewStatus.ACTIVE
    )


def get_review_aggregate(obj):
    """
    Utility function to get the review aggregate for any model instance.
    Creates one if it doesn't exist.
    
    Usage:
        aggregate = get_review_aggregate(nurse_instance)
        print(f"Average: {aggregate.average_rating}, Count: {aggregate.review_count}")
    """
    content_type = ContentType.objects.get_for_model(obj)
    aggregate, _ = ReviewAggregate.objects.get_or_create(
        content_type=content_type,
        object_id=str(obj.pk)
    )
    return aggregate


def create_review(reviewer, reviewed_object, rating, text='', title='', image=None, context_object=None):
    """
    Utility function to create a review with proper content type handling.
    
    Usage:
        review = create_review(
            reviewer=patient_user,
            reviewed_object=nurse_provider,
            rating=5,
            text="Excellent service!",
            context_object=nurse_service_request
        )
    """
    reviewed_content_type = ContentType.objects.get_for_model(reviewed_object)
    
    context_content_type = None
    context_object_id = None
    if context_object:
        context_content_type = ContentType.objects.get_for_model(context_object)
        context_object_id = str(context_object.pk)
    
    review = Review.objects.create(
        reviewer=reviewer,
        reviewed_content_type=reviewed_content_type,
        reviewed_object_id=str(reviewed_object.pk),
        context_content_type=context_content_type,
        context_object_id=context_object_id,
        rating=rating,
        title=title,
        text=text,
        image=image
    )
    
    return review
