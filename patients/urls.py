"""
URL configuration for patients app.

Endpoints:
- /api/patients/ - Patient record CRUD (providers)
- /api/patients/me/ - Get my patient record (patients)
- /api/patients/link-account/ - Link account to record (patients)
- /api/patients/share-tokens/ - Manage share tokens (patients)
- /api/patients/records/share/{token}/ - Access via share token (providers)
- /api/patients/{id}/history/ - Patient medical history (providers)
- /api/patients/my-records/ - My medical records (patients)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from patients.views import (
    PatientRecordViewSet,
    ShareTokenViewSet,
    link_patient_account,
    my_patient_record,
    access_via_share_token,
    my_share_tokens,
    my_medical_records,
    patient_medical_history,
)

app_name = 'patients'

# Main router for patient records
router = DefaultRouter()
router.register(r'', PatientRecordViewSet, basename='patient-record')

# Share token router
share_token_router = DefaultRouter()
share_token_router.register(r'', ShareTokenViewSet, basename='share-token')

urlpatterns = [
    # Link account endpoint (must be before router to avoid conflict)
    path('link-account/', link_patient_account, name='link-account'),
    
    # Get my patient record
    path('me/', my_patient_record, name='my-patient-record'),
    
    # My medical records (patient view)
    path('my-records/', my_medical_records, name='my-medical-records'),
    
    # My share tokens (patient view)
    path('my-share-tokens/', my_share_tokens, name='my-share-tokens'),
    
    # Share tokens management
    path('share-tokens/', include(share_token_router.urls)),
    
    # Access records via share token (for providers)
    path('records/share/<str:token>/', access_via_share_token, name='access-via-share-token'),
    
    # Patient medical history (for providers)
    path('<int:patient_id>/history/', patient_medical_history, name='patient-medical-history'),
    
    # Router URLs (at the end to avoid conflicts)
    path('', include(router.urls)),
]
