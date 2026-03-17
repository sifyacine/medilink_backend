"""Admins serializers."""
from admins.serializers.provider_review import (
    ProviderListSerializer,
    ProviderRefuseSerializer,
)
from admins.serializers.users import (
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    AdminUserUpdateSerializer,
    AdminUserSuspendSerializer,
)
from admins.serializers.patients import (
    AdminPatientListSerializer,
    AdminPatientDetailSerializer,
)
from admins.serializers.analytics import (
    OverviewStatsSerializer,
    TimeSeriesPointSerializer,
    ProviderTypeStatSerializer,
    AppointmentStatusStatSerializer,
    RevenueByMonthSerializer,
    PaymentMethodStatSerializer,
)
from admins.serializers.activity_log import AdminActivityLogSerializer
from admins.serializers.invoices import (
    AdminInvoiceListSerializer,
    AdminInvoiceDetailSerializer,
)
from admins.serializers.products import (
    MediLinkProductSerializer,
    MediLinkProductListSerializer,
    MediLinkSaleSerializer,
)

__all__ = [
    'ProviderListSerializer',
    'ProviderRefuseSerializer',
    'AdminUserListSerializer',
    'AdminUserDetailSerializer',
    'AdminUserUpdateSerializer',
    'AdminUserSuspendSerializer',
    'AdminPatientListSerializer',
    'AdminPatientDetailSerializer',
    'OverviewStatsSerializer',
    'TimeSeriesPointSerializer',
    'ProviderTypeStatSerializer',
    'AppointmentStatusStatSerializer',
    'RevenueByMonthSerializer',
    'PaymentMethodStatSerializer',
    'AdminActivityLogSerializer',
    'AdminInvoiceListSerializer',
    'AdminInvoiceDetailSerializer',
    'MediLinkProductSerializer',
    'MediLinkProductListSerializer',
    'MediLinkSaleSerializer',
]
