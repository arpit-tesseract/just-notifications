from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from configuration.models import ModelAccess

# class HasCustomAccessPermission(BasePermission):
#     """
#     Permission for system users with module+action access.
#     Works with both ViewSets and FBVs.
#     """

#     def has_permission(self, request, view):
#         user = request.user

#         if not (user and user.is_authenticated):
#             raise PermissionDenied("Authentication required")

#         # if not getattr(user, "is_system_user", False):
#         #     raise PermissionDenied("Only system users can access this API")

#         # Map HTTP methods to CRUD actions
#         method_action_map = {
#             "GET": "read",
#             "POST": "create",
#             "PUT": "update",
#             "PATCH": "update",
#             "DELETE": "delete",
#         }

#         # Determine CRUD action
#         if hasattr(view, "action"):  # ViewSet
#             action_map = {
#                 "create": "create",
#                 "list": "read",
#                 "retrieve": "read",
#                 "update": "update",
#                 "partial_update": "update",
#                 "destroy": "delete",
#             }
#             crud_action = action_map.get(view.action)
#         else:  # FBV
#             crud_action = method_action_map.get(request.method)

#         if not crud_action:
#             raise PermissionDenied("Invalid request action")

#         # Extract module_name
#         module_name = getattr(request, "module_name", None)  # FBV-safe
#         print("Module name from request:", module_name)
#         if module_name is None:
#             # Try ViewSet-style fallback
#             module_name = getattr(view, "module_name", None) \
#                           or getattr(view, "cls", None) and getattr(view.cls, "module_name", None) \
#                           or getattr(view, "view_class", None) and getattr(view.view_class, "module_name", None) \
#                           or getattr(view, "initkwargs", {}).get("module_name") \
#                           or getattr(view, "kwargs", {}).get("module_name")
#             print("Module name from view fallback:", module_name)

#         if not module_name:
#             raise PermissionDenied("Module name not defined for this API")

#         # Check access
#         if not user.access.filter(
#             module__name=module_name,
#             permission__name=crud_action,
#             on_hold=False,
#             is_hidden=False,
#         ).exists():
#             raise PermissionDenied(f"You lack {crud_action} permission for {module_name}")

#         return True


from rest_framework.permissions import BasePermission

class HasModelAccessPermission(BasePermission):
    """
    Checks if the user has access to the model and the requested CRUD operation.
    """

    def has_permission(self, request, view):
        # Get user and action from request
        user = request.user
        model_name = view.queryset.model._meta.label  # e.g., "yourapp.City"

        action = view.action  # 'list', 'retrieve', 'create', 'update', 'destroy'

        # Map DRF action to model permissions
        action_map = {
            'list': 'can_read',
            'retrieve': 'can_read',
            'create': 'can_create',
            'update': 'can_update',
            'partial_update': 'can_update',
            'destroy': 'can_delete',
        }

        # Check if user is authenticated
        if not user.is_authenticated:
            return False

        # Fetch model access
        try:
            print(model_name)
            model_access = user.model_access_rule.get(model__technical_name=model_name)
        except ModelAccess.DoesNotExist:
            return False

        perm_field = action_map.get(action) # e.g., "can_read"
        return getattr(model_access, perm_field, False) # e.g., model_access.can_read or False
