"""Scoping permissions for the e-commerce module, built on existing user role helpers."""
from rest_framework.permissions import BasePermission


def is_platform_admin(user):
    """Shashan admin / super admin (platform-wide access)."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True
    try:
        if user.is_super_admin() or user.is_admin():
            return True
    except Exception:
        pass
    return False


def user_business_family_ids(user):
    """BusinessFamily ids this user belongs to (as an active member/owner)."""
    if not user or not user.is_authenticated:
        return []
    from user.models import BusinessFamilyMember
    return list(
        BusinessFamilyMember.objects
        .filter(user=user, is_active=True)
        .values_list('business_family_id', flat=True)
    )


class IsAdminIdentity(BasePermission):
    """Only Shashan admins may manage master config and route orders."""
    message = "Admin (Shashan) access is required for this action."

    def has_permission(self, request, view):
        return is_platform_admin(request.user)


class IsAuthenticatedBusinessOrAdmin(BasePermission):
    """
    Read for any authenticated user; writes for admins or business members.
    Object-level scoping to the caller's own business is done in the view querysets.
    """
    message = "You do not have permission to manage this merchant resource."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if is_platform_admin(user):
            return True
        return bool(user_business_family_ids(user))
