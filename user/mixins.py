from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from django.db import models
from user.models import UserRole


class IsSuperAdmin(BasePermission):
    """
    Grants access only to users whose role is 'super_admin'.
    Used to guard endpoints that must be exclusively controlled by
    the Super Admin (e.g., System Admin registration — SRS 5.1).
    """
    message = "Only Super Admins are permitted to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_super_admin()
        )

class IsAdminRole(BasePermission):
    """
    Allows access to any user who holds a role within the 'admin' hierarchy
    (super_admin, system_admin, group_admin, subgroup_admin, etc.).

    The *scope* of what they can manage is enforced separately in each view
    using AdminRoleFilterMixin.get_allowed_role_ids().
    """
    message = "Only Admin users are permitted to perform this action."

    @staticmethod
    def _is_in_admin_hierarchy(role):
        """Walk up the parent chain to see if 'admin' is an ancestor."""
        current = role
        while current:
            if current.name == 'admin':
                return True
            current = current.parent
        return False

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # Super admin always passes
        if request.user.is_super_admin():
            return True
        # Any role inside the admin hierarchy passes
        return any(
            self._is_in_admin_hierarchy(r)
            for r in request.user.roles.select_related('parent').all()
        )


class AdminRoleFilterMixin:
    def get_allowed_role_ids(self, request, requested_role_name):
        """
        Returns a tuple of (role_ids_list, error_response).
        If error_response is not None, the view should return it.
        """
        if requested_role_name == "admin":
            user = request.user
            
            # Find the user's role that belongs to the admin hierarchy
            user_roles = user.roles.select_related('parent').all()
            
            def is_admin_hierarchy(r):
                current = r
                while current:
                    if current.name == 'admin':
                        return True
                    current = current.parent
                return False
                
            user_admin_role = None
            for r in user_roles:
                if is_admin_hierarchy(r):
                    # We assume the user has at most one admin role.
                    user_admin_role = r
                    break
                    
            if not user_admin_role:
                # If the user is not in the admin hierarchy, they see no admin users.
                return [], None
                
            # Get all descendants of user_admin_role
            descendant_ids = []
            def get_descendants(role_obj):
                children = UserRole.objects.filter(parent=role_obj)
                for child in children:
                    descendant_ids.append(child.id)
                    get_descendants(child)
            
            get_descendants(user_admin_role)
            return descendant_ids, None
            
        else:
            # Default behavior for non-admin roles
            role = UserRole.objects.filter(name=requested_role_name).first()
            if not role:
                return [], Response({"detail": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)
                
            role_ids = UserRole.objects.filter(
                models.Q(id=role.id) | models.Q(parent=role)
            ).values_list("id", flat=True)
            return list(role_ids), None
