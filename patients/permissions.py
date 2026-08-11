from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User

STAFF_ROLES = {User.Role.ADMIN, User.Role.DOCTOR, User.Role.RECEPTIONIST}


class IsSelfOrStaff(BasePermission):
    """Patient can access only their own record. Admin/doctor/receptionist can access any (for care/booking)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role in STAFF_ROLES:
            return True
        return obj.user_id == user.id
