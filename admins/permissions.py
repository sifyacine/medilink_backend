"""
Admins app permissions — base IsAdmin plus sub-role permission classes.
"""
from rest_framework.permissions import BasePermission

from common.permissions import IsAdmin
from common.enums import UserRole, AdminSubRole


def _get_sub_role(user):
    """Safely fetch admin sub_role; returns None if not set."""
    try:
        return user.admin_profile.sub_role
    except Exception:
        return None


class IsSuperAdmin(BasePermission):
    """User must be ADMIN with sub_role == SUPER_ADMIN."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != UserRole.ADMIN or not request.user.can_login:
            return False
        return _get_sub_role(request.user) == AdminSubRole.SUPER_ADMIN


class IsModerator(BasePermission):
    """User must be ADMIN with sub_role SUPER_ADMIN or MODERATOR."""

    _allowed = {AdminSubRole.SUPER_ADMIN, AdminSubRole.MODERATOR}

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != UserRole.ADMIN or not request.user.can_login:
            return False
        return _get_sub_role(request.user) in self._allowed


class IsSupport(BasePermission):
    """User must be ADMIN with sub_role SUPER_ADMIN, MODERATOR, or SUPPORT."""

    _allowed = {AdminSubRole.SUPER_ADMIN, AdminSubRole.MODERATOR, AdminSubRole.SUPPORT}

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != UserRole.ADMIN or not request.user.can_login:
            return False
        return _get_sub_role(request.user) in self._allowed


class IsContentEditor(BasePermission):
    """User must be ADMIN with sub_role SUPER_ADMIN or CONTENT_EDITOR."""

    _allowed = {AdminSubRole.SUPER_ADMIN, AdminSubRole.CONTENT_EDITOR}

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != UserRole.ADMIN or not request.user.can_login:
            return False
        return _get_sub_role(request.user) in self._allowed


__all__ = [
    'IsAdmin',
    'IsSuperAdmin',
    'IsModerator',
    'IsSupport',
    'IsContentEditor',
]
