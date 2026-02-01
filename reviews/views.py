"""Views for the reviews app."""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from reviews.models import Review, ReviewAggregate, ReviewHelpful, ReviewStatus
from reviews.serializers import (
    ReviewSerializer, ReviewCreateSerializer, ReviewListSerializer,
    ReviewResponseSerializer, ReviewAggregateSerializer,
    BulkReviewStatsSerializer
)
from reviews.permissions import IsReviewerOrReadOnly, CanRespondToReview, IsAdminOrReadOnly


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    
    Endpoints:
    - GET /reviews/ - List all active reviews
    - POST /reviews/ - Create a new review
    - GET /reviews/{id}/ - Get review details
    - PUT/PATCH /reviews/{id}/ - Update a review (reviewer only)
    - DELETE /reviews/{id}/ - Soft delete a review (reviewer only)
    - POST /reviews/{id}/respond/ - Add response to review (reviewed entity owner)
    - POST /reviews/{id}/helpful/ - Mark review as helpful
    - DELETE /reviews/{id}/helpful/ - Remove helpful mark
    - POST /reviews/{id}/flag/ - Flag review for moderation
    """
    queryset = Review.objects.filter(status=ReviewStatus.ACTIVE)
    permission_classes = [IsReviewerOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        if self.action == 'list':
            return ReviewListSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        """Filter reviews by target if specified."""
        queryset = Review.objects.filter(status=ReviewStatus.ACTIVE)
        
        # Filter by target type and ID
        target_type = self.request.query_params.get('target_type')
        target_id = self.request.query_params.get('target_id')
        
        if target_type and target_id:
            try:
                content_type = ContentType.objects.get(model=target_type.lower())
                queryset = queryset.filter(
                    reviewed_content_type=content_type,
                    reviewed_object_id=target_id
                )
            except ContentType.DoesNotExist:
                queryset = queryset.none()
        
        # Filter by context
        context_type = self.request.query_params.get('context_type')
        context_id = self.request.query_params.get('context_id')
        
        if context_type and context_id:
            try:
                content_type = ContentType.objects.get(model=context_type.lower())
                queryset = queryset.filter(
                    context_content_type=content_type,
                    context_object_id=context_id
                )
            except ContentType.DoesNotExist:
                pass
        
        # Filter by reviewer
        reviewer_id = self.request.query_params.get('reviewer_id')
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)
        
        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        max_rating = self.request.query_params.get('max_rating')
        
        if min_rating:
            queryset = queryset.filter(rating__gte=int(min_rating))
        if max_rating:
            queryset = queryset.filter(rating__lte=int(max_rating))
        
        return queryset.select_related('reviewer', 'reviewed_content_type')
    
    def perform_destroy(self, instance):
        """Soft delete the review."""
        instance.soft_delete()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def respond(self, request, pk=None):
        """Add a response to a review."""
        review = self.get_object()
        
        # Check permission (reviewed entity owner or admin)
        if not CanRespondToReview().has_object_permission(request, self, review):
            return Response(
                {'error': 'You do not have permission to respond to this review.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ReviewResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review.add_response(
            response_text=serializer.validated_data['response'],
            response_by=request.user
        )
        
        return Response(ReviewSerializer(review).data)
    
    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def helpful(self, request, pk=None):
        """Mark or unmark a review as helpful."""
        review = self.get_object()
        
        if request.method == 'POST':
            helpful, created = ReviewHelpful.objects.get_or_create(
                review=review,
                user=request.user
            )
            if created:
                return Response({'message': 'Review marked as helpful.'})
            return Response({'message': 'Already marked as helpful.'})
        
        else:  # DELETE
            deleted, _ = ReviewHelpful.objects.filter(
                review=review,
                user=request.user
            ).delete()
            if deleted:
                return Response({'message': 'Helpful mark removed.'})
            return Response({'message': 'Not marked as helpful.'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def flag(self, request, pk=None):
        """Flag a review for moderation."""
        review = self.get_object()
        review.flag()
        return Response({'message': 'Review flagged for moderation.'})


class MyReviewsView(generics.ListAPIView):
    """
    List all reviews by the authenticated user.
    
    GET /reviews/my-reviews/
    """
    serializer_class = ReviewListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(
            reviewer=self.request.user
        ).exclude(status=ReviewStatus.DELETED)


class ReviewsReceivedView(generics.ListAPIView):
    """
    List all reviews received by the authenticated user's entities.
    For providers: reviews on their profile.
    
    GET /reviews/received/
    """
    serializer_class = ReviewListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get reviews for user directly
        user_ct = ContentType.objects.get_for_model(user)
        queryset = Review.objects.filter(
            reviewed_content_type=user_ct,
            reviewed_object_id=str(user.pk),
            status=ReviewStatus.ACTIVE
        )
        
        # If user is a provider, get reviews for their provider profile
        if hasattr(user, 'provider_profile'):
            provider = user.provider_profile
            provider_ct = ContentType.objects.get_for_model(provider)
            queryset = queryset | Review.objects.filter(
                reviewed_content_type=provider_ct,
                reviewed_object_id=str(provider.pk),
                status=ReviewStatus.ACTIVE
            )
        
        return queryset.order_by('-created_at')


class ReviewAggregateView(generics.RetrieveAPIView):
    """
    Get review aggregate for a specific entity.
    
    GET /reviews/aggregate/?target_type=provider&target_id=123
    """
    serializer_class = ReviewAggregateSerializer
    permission_classes = [AllowAny]
    
    def get_object(self):
        target_type = self.request.query_params.get('target_type')
        target_id = self.request.query_params.get('target_id')
        
        if not target_type or not target_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('target_type and target_id are required.')
        
        try:
            content_type = ContentType.objects.get(model=target_type.lower())
        except ContentType.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f'Invalid target_type: {target_type}')
        
        aggregate, _ = ReviewAggregate.objects.get_or_create(
            content_type=content_type,
            object_id=target_id
        )
        return aggregate


class BulkReviewStatsView(generics.GenericAPIView):
    """
    Get review stats for multiple entities at once.
    Useful for list views where you need ratings for multiple items.
    
    POST /reviews/bulk-stats/
    {
        "target_type": "provider",
        "target_ids": ["1", "2", "3"]
    }
    """
    serializer_class = BulkReviewStatsSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_type = serializer.validated_data['target_type']
        target_ids = serializer.validated_data['target_ids']
        
        content_type = ContentType.objects.get(model=target_type)
        
        # Get or create aggregates for all targets
        aggregates = {}
        for target_id in target_ids:
            aggregate, _ = ReviewAggregate.objects.get_or_create(
                content_type=content_type,
                object_id=target_id
            )
            aggregates[target_id] = {
                'average_rating': float(aggregate.average_rating),
                'review_count': aggregate.review_count,
            }
        
        return Response(aggregates)
