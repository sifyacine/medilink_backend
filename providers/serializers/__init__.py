"""Providers serializers."""
from providers.serializers.status import ProviderStatusSerializer
from providers.serializers.provider import (
    ProviderPublicSerializer,
    ProviderDetailSerializer,
)
from providers.serializers.clinic import ClinicSerializer, ClinicCreateSerializer
from providers.serializers.laboratory import LaboratorySerializer, LaboratoryCreateSerializer
from providers.serializers.seller import SellerSerializer, SellerCreateSerializer
from providers.serializers.vtc import VTCSerializer, VTCCreateSerializer

__all__ = [
    'ProviderStatusSerializer',
    'ProviderPublicSerializer',
    'ProviderDetailSerializer',
    'ClinicSerializer',
    'ClinicCreateSerializer',
    'LaboratorySerializer',
    'LaboratoryCreateSerializer',
    'SellerSerializer',
    'SellerCreateSerializer',
    'VTCSerializer',
    'VTCCreateSerializer',
]
