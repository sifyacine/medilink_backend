"""
Django admin configuration for providers app.
"""
from django.contrib import admin

from providers.models import (
    Provider,
    Doctor,
    Nurse,
    Clinic,
    Laboratory,
    VTC,
    Seller,
    ProviderStatusHistory,
)


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    """Admin interface for Provider model."""
    list_display = ['user', 'provider_type', 'status', 'verified_at', 'created_at']
    list_filter = ['status', 'provider_type', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']
    ordering = ['-created_at']


@admin.register(ProviderStatusHistory)
class ProviderStatusHistoryAdmin(admin.ModelAdmin):
    """Admin interface for ProviderStatusHistory model."""
    list_display = ['provider', 'old_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['provider__user__email', 'reason']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


# Register subtype models
from providers.models.doctor import Doctor, DoctorCertification
from providers.models.nurse import Nurse, NurseCertification
from providers.models.clinic import Clinic
from providers.models.laboratory import Laboratory
from providers.models.vtc import VTC
from providers.models.seller import Seller

admin.site.register(Doctor)
admin.site.register(DoctorCertification)
admin.site.register(Nurse)
admin.site.register(NurseCertification)
admin.site.register(Clinic)
admin.site.register(Laboratory)
admin.site.register(VTC)
admin.site.register(Seller)
