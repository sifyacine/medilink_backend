from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NursingServiceViewSet,
    PatientNurseRequestViewSet,
    NurseAvailableRequestsViewSet,
    NurseMyOffersViewSet,
    NurseProfileServicesViewSet,
    NurseRequestHistoryViewSet
)

# Router for standard CRUD operations
router = DefaultRouter()
router.register(r'services', NursingServiceViewSet, basename='nursing-services')

# Patient router
patient_router = DefaultRouter()
patient_router.register(
    r'nurse-requests',
    PatientNurseRequestViewSet,
    basename='patient-nurse-requests'
)

# Nurse router
nurse_router = DefaultRouter()
nurse_router.register(
    r'available-requests',
    NurseAvailableRequestsViewSet,
    basename='nurse-available-requests'
)
nurse_router.register(
    r'my-offers',
    NurseMyOffersViewSet,
    basename='nurse-my-offers'
)
nurse_router.register(
    r'my-services',
    NurseProfileServicesViewSet,
    basename='nurse-my-services'
)
nurse_router.register(
    r'request-history',
    NurseRequestHistoryViewSet,
    basename='nurse-request-history'
)

urlpatterns = [
    # Common endpoints (services catalog)
    path('', include(router.urls)),

    # Patient endpoints
    path('patient/', include(patient_router.urls)),

    # Nurse endpoints
    path('nurse/', include(nurse_router.urls)),
]
