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
    AdminServiceViewSet,
    AdminNurseServiceViewSet,
    AdminDoctorServiceViewSet,
    AdminProviderCustomServiceViewSet,
    AdminSpecialtyViewSet,
    AdminDoctorSpecialtyViewSet,
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
router.register(r'services', AdminServiceViewSet, basename='admin-services')
router.register(r'nurse-services', AdminNurseServiceViewSet, basename='admin-nurse-services')
router.register(r'doctor-services', AdminDoctorServiceViewSet, basename='admin-doctor-services')
router.register(r'custom-services', AdminProviderCustomServiceViewSet, basename='admin-custom-services')
router.register(r'specialties', AdminSpecialtyViewSet, basename='admin-specialties')
router.register(r'doctor-specialties', AdminDoctorSpecialtyViewSet, basename='admin-doctor-specialties')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/overview/', OverviewView.as_view(), name='analytics-overview'),
    path('analytics/users/', UserStatsView.as_view(), name='analytics-users'),
    path('analytics/appointments/', AppointmentStatsView.as_view(), name='analytics-appointments'),
    path('analytics/revenue/', RevenueStatsView.as_view(), name='analytics-revenue'),
    path('analytics/providers/', ProviderStatsView.as_view(), name='analytics-providers'),
]
