"""
Admins app permissions.
All admin users have equal access to all admin features.
No sub-roles: any user with role == ADMIN can do everything.
"""
from common.permissions import IsAdmin

# Re-export IsAdmin as the single permission used across all admin views.
# IsModerator / IsSupport / IsSuperAdmin / IsContentEditor are kept as aliases
# for backward compatibility but are all equivalent to IsAdmin.
IsSuperAdmin = IsAdmin
IsModerator = IsAdmin
IsSupport = IsAdmin
IsContentEditor = IsAdmin

__all__ = [
    'IsAdmin',
    'IsSuperAdmin',
    'IsModerator',
    'IsSupport',
    'IsContentEditor',
]
