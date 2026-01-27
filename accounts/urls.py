"""
URL configuration for accounts app.
"""
from django.urls import path

from accounts.views import (
    login,
    logout,
    patient_register,
    provider_register,
    get_my_profile,
    check_account_status,
)

# Import password reset if available
try:
    from accounts.views.password_reset import (
        password_reset_request,
        password_reset_confirm,
    )
    PASSWORD_RESET_AVAILABLE = True
except ImportError:
    PASSWORD_RESET_AVAILABLE = False

app_name = 'accounts'

urlpatterns = [
    # Patient registration
    path('patient/register/', patient_register, name='patient-register'),
    
    # Provider registration
    path('provider/register/', provider_register, name='provider-register'),
    
    # Authentication
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    
    # Profile self-management (GET, PATCH, PUT on same endpoint)
    path('me/', get_my_profile, name='me'),

    # Public account status check by email
    path('status/', check_account_status, name='check-account-status'),
]

# Add password reset endpoints if available
if PASSWORD_RESET_AVAILABLE:
    urlpatterns += [
        path('password/reset/', password_reset_request, name='password-reset-request'),
        path('password/reset/confirm/', password_reset_confirm, name='password-reset-confirm'),
    ]
