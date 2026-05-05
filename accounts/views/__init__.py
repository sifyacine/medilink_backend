"""Accounts views."""
from accounts.views.auth import login, logout
from accounts.views.registration import patient_register, provider_register
from accounts.views.profile import get_my_profile
from accounts.views.status import check_account_status
from accounts.views.user_profile import change_password

# Import password reset views if they exist
try:
    from accounts.views.password_reset import (
        password_reset_request,
        password_reset_confirm,
    )
    __all__ = [
        'login',
        'logout',
        'patient_register',
        'provider_register',
        'get_my_profile',
        'change_password',
        'check_account_status',
        'password_reset_request',
        'password_reset_confirm',
    ]
except ImportError:
    __all__ = [
        'login',
        'logout',
        'patient_register',
        'provider_register',
        'get_my_profile',
        'change_password',
        'check_account_status',
    ]
