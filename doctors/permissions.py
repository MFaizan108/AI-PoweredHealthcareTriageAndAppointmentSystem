from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User


class IsAdminOrOwnerDoctorOrReadOnly(BasePermission):
    """Anyone authenticated can read. Admin can write anything. A doctor can write only their own record."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return True
        doctor = obj if hasattr(obj, "user") and obj.__class__.__name__ == "Doctor" else getattr(obj, "doctor", None)
        return bool(doctor and doctor.user_id == request.user.id)
