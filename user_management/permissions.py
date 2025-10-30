from rest_framework.permissions import BasePermission

class SystemAdminPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.check_is_system_admin() and request.user.is_verified