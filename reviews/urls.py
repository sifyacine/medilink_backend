"""URL configuration for the reviews app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from reviews.views import (
    ReviewViewSet, MyReviewsView, ReviewsReceivedView,
    ReviewAggregateView, BulkReviewStatsView
)

router = DefaultRouter()
router.register(r'', ReviewViewSet, basename='review')

urlpatterns = [
    path('my-reviews/', MyReviewsView.as_view(), name='my-reviews'),
    path('received/', ReviewsReceivedView.as_view(), name='reviews-received'),
    path('aggregate/', ReviewAggregateView.as_view(), name='review-aggregate'),
    path('bulk-stats/', BulkReviewStatsView.as_view(), name='bulk-review-stats'),
    path('', include(router.urls)),
]
