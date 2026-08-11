from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User


class IsAdminOrReadOnlyForAuthenticated(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(user.is_superuser or user.role == User.Role.ADMIN)
