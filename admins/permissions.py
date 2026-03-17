"""
Admins app permissions.
All admin users have equal access to all admin features.
No sub-roles: any user with role == ADMIN can do everything.
"""
from rest_framework.permissions import BasePermission

from common.permissions import IsAdmin
from common.enums import UserRole, ProviderType

# Re-export IsAdmin as the single permission used across all admin views.
# IsModerator / IsSupport / IsSuperAdmin / IsContentEditor are kept as aliases
# for backward compatibility but are all equivalent to IsAdmin.
IsSuperAdmin = IsAdmin
IsModerator = IsAdmin
IsSupport = IsAdmin
IsContentEditor = IsAdmin


class IsAdminOrSeller(BasePermission):
    """Allow access to ADMIN users and PROVIDER users with SELLER provider type."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        if user.role == UserRole.ADMIN and getattr(user, 'can_login', True):
            return True

        if user.role != UserRole.PROVIDER or not getattr(user, 'can_login', True):
            return False

        try:
            return user.provider_profile.provider_type == ProviderType.SELLER
        except Exception:
            return False

__all__ = [
    'IsAdmin',
    'IsSuperAdmin',
    'IsModerator',
    'IsSupport',
    'IsContentEditor',
    'IsAdminOrSeller',
]
