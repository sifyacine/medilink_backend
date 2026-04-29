"""
URL configuration for admins app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from admins.views import (
    AdminProviderViewSet,
    UserManagementViewSet,
    AdminPatientViewSet,
    AdminActivityLogViewSet,
    AdminInvoiceViewSet,
    MediLinkProductViewSet,
    MediLinkIncomeViewSet,
    OverviewView,
    UserStatsView,
    AppointmentStatsView,
    RevenueStatsView,
    ProviderStatsView,
    AdminSocialMediaLinkViewSet,
)

app_name = 'admins'

router = DefaultRouter()
router.register(r'providers', AdminProviderViewSet, basename='admin-provider')
router.register(r'users', UserManagementViewSet, basename='admin-users')
router.register(r'patients', AdminPatientViewSet, basename='admin-patients')
router.register(r'logs', AdminActivityLogViewSet, basename='admin-activity-logs')
router.register(r'invoices', AdminInvoiceViewSet, basename='admin-invoices')
router.register(r'products', MediLinkProductViewSet, basename='admin-products')
router.register(r'income', MediLinkIncomeViewSet, basename='admin-income')
router.register(r'social-links', AdminSocialMediaLinkViewSet, basename='admin-social-links')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/overview/', OverviewView.as_view(), name='analytics-overview'),
    path('analytics/users/', UserStatsView.as_view(), name='analytics-users'),
    path('analytics/appointments/', AppointmentStatsView.as_view(), name='analytics-appointments'),
    path('analytics/revenue/', RevenueStatsView.as_view(), name='analytics-revenue'),
    path('analytics/providers/', ProviderStatsView.as_view(), name='analytics-providers'),
]
