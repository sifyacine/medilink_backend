"""Providers views."""
from providers.views.status import provider_status
from providers.views.clinic import ClinicViewSet
from providers.views.laboratory import LaboratoryViewSet
from providers.views.seller import SellerViewSet
from providers.views.vtc import VTCViewSet

__all__ = [
    'provider_status',
    'ClinicViewSet',
    'LaboratoryViewSet',
    'SellerViewSet',
    'VTCViewSet',
]
