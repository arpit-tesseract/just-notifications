from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from configuration.models import ModelAccess

from rest_framework.permissions import BasePermission

# Working for APIView & Model ViewSet
class HasModelAccessPermission(BasePermission):
    """
    Checks if the user has access to the model and the requested CRUD operation.
    Supports both ViewSets (with .action) and APIViews (with HTTP method).
    """
    
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        # Super Admin of system user
        if user.check_is_super_admin():
            return True

        # Resolve model from queryset or model attr
        elif hasattr(view, "model") and view.model is not None:
            model_name = view.model._meta.label
        elif hasattr(view, "get_base_queryset") and view.get_base_queryset is not None:
            model_name = view.get_base_queryset().model._meta.label
        if hasattr(view, "queryset") and view.queryset is not None:
            model_name = view.queryset.model._meta.label
        else:
            raise AttributeError(
                f"{view.__class__.__name__} must define either `queryset` or `model`"
            )

        # Try to get action (ViewSet) or fall back to HTTP method (APIView)
        action = getattr(view, "action", None)
        if not action:  
            action = request.method.lower()

        # Map to your permission fields
        action_map = {
            # ViewSet actions
            "list": "can_read",
            "retrieve": "can_read",
            "create": "can_create",
            "update": "can_update",
            "partial_update": "can_update",
            "destroy": "can_delete",
            # HTTP verbs → same mapping
            "get": "can_read",
            "post": "can_create",
            "put": "can_update",
            "patch": "can_update",
            "delete": "can_delete",
        }

        perm_field = action_map.get(action)
        if not perm_field:
            return False

        # Fetch model access
        try:
            model_access = user.model_access_rule.get(model__technical_name=model_name)
        except ModelAccess.DoesNotExist:
            return False
        except Exception as e:
            return False

        return getattr(model_access, perm_field, False)


# Only work for Model ViewSet
# class HasModelAccessPermission(BasePermission):
#     """
#     Checks if the user has access to the model and the requested CRUD operation.
#     """

#     def has_permission(self, request, view):
#         # Get user and action from request
#         user = request.user
#         model_name = view.queryset.model._meta.label  # e.g., "yourapp.City"

#         action = view.action  # 'list', 'retrieve', 'create', 'update', 'destroy'

#         # Map DRF action to model permissions
#         action_map = {
#             'list': 'can_read',
#             'retrieve': 'can_read',
#             'create': 'can_create',
#             'update': 'can_update',
#             'partial_update': 'can_update',
#             'destroy': 'can_delete',
#         }

#         # Check if user is authenticated
#         if not user.is_authenticated:
#             return False

#         # Fetch model access
#         try:
#             print(model_name)
#             model_access = user.model_access_rule.get(model__technical_name=model_name)
#         except ModelAccess.DoesNotExist:
#             return False

#         perm_field = action_map.get(action) # e.g., "can_read"
#         return getattr(model_access, perm_field, False) # e.g., model_access.can_read or False
