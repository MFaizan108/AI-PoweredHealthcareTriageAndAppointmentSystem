from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user and request.user.is_authenticated and (request.user.role == User.Role.ADMIN or request.user.is_superuser)
        )
