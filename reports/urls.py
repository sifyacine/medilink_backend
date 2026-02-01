"""URL configuration for the reports app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from reports.views import ReportViewSet, ReportAggregateViewSet, UserBanViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'aggregates', ReportAggregateViewSet, basename='report-aggregate')
router.register(r'bans', UserBanViewSet, basename='user-ban')

urlpatterns = [
    path('', include(router.urls)),
]
