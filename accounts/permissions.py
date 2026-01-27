"""Accounts app permissions."""
from common.permissions import (
    IsPatient,
    IsProvider,
    IsAdmin,
)

__all__ = ['IsPatient', 'IsProvider', 'IsAdmin']
