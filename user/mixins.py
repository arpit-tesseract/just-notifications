from rest_framework.response import Response
from rest_framework import status
from django.db import models
from user.models import UserRole

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
