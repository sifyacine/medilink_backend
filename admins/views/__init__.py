"""Admins views."""
from admins.views.provider_review import AdminProviderViewSet
from admins.views.users import UserManagementViewSet
from admins.views.patients import AdminPatientViewSet
from admins.views.analytics import (
        OverviewView,
        UserStatsView,
        AppointmentStatsView,
        RevenueStatsView,
        ProviderStatsView,
)
from admins.views.activity_log import AdminActivityLogViewSet
from admins.views.invoices import AdminInvoiceViewSet
from admins.views.products import MediLinkProductViewSet, MediLinkIncomeViewSet
from admins.views.public_products import PublicProductViewSet

__all__ = [
        'AdminProviderViewSet',
        'UserManagementViewSet',
        'AdminPatientViewSet',
        'OverviewView',
        'UserStatsView',
        'AppointmentStatsView',
        'RevenueStatsView',
        'ProviderStatsView',
        'AdminActivityLogViewSet',
        'AdminInvoiceViewSet',
        'MediLinkProductViewSet',
        'MediLinkIncomeViewSet',
        'PublicProductViewSet',
]
