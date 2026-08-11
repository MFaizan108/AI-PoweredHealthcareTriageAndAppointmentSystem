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
        # view.action reliably distinguishes "create" from other POST-based custom actions (e.g. "review")
        # on TriageAssessmentViewSet. Plain APIViews (TriageAssessView) have no .action, so fall back to method.
        action = getattr(view, "action", None)
        is_create = action == "create" if action is not None else request.method == "POST"
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
