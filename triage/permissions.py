from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User


class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role == User.Role.ADMIN))


class IsAdminOrReadOnlyForAuthenticated(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(user.is_superuser or user.role == User.Role.ADMIN)


class CanAccessTriageAssessment(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        is_create = getattr(view, "action", None) == "create" or request.method == "POST"
        if is_create:
            return bool(user.is_superuser or user.role in (User.Role.PATIENT, User.Role.ADMIN, User.Role.RECEPTIONIST))
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            return True
        if user.role == User.Role.PATIENT:
            return obj.patient.user_id == user.id
        if user.role == User.Role.DOCTOR:
            return bool(obj.appointment and obj.appointment.doctor.user_id == user.id)
        return False
