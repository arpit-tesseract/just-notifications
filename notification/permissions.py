from typing import Any

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Allow authenticated users to read, but restrict writes to staff/admin users."""

    message = "You do not have permission to perform this action."

    def has_permission(self, request: Any, view: Any) -> bool:
        """Authorize read access for authenticated users and write access for admins only."""
        if not getattr(request.user, "is_authenticated", False):
            return False

        if request.method in SAFE_METHODS:
            return True

        return bool(getattr(request.user, "is_staff", False))
