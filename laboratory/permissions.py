from rest_framework.permissions import BasePermission

from accounts.models import User


def _check_lab_access(user, patient, requested_by, method):
    if user.is_superuser or user.role in (User.Role.ADMIN, User.Role.LAB_STAFF):
        return True
    if user.role == User.Role.PATIENT:
        return patient.user_id == user.id and method in ("GET", "HEAD", "OPTIONS")
    if user.role == User.Role.DOCTOR:
        return bool(requested_by and requested_by.user_id == user.id)
    return False


class CanAccessLabTest(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if view.action == "create":
            return bool(user.is_superuser or user.role in (User.Role.DOCTOR, User.Role.ADMIN, User.Role.LAB_STAFF))
        return True

    def has_object_permission(self, request, view, obj):
        return _check_lab_access(request.user, obj.patient, obj.requested_by, request.method)


class CanAccessLabReport(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if view.action == "create":
            return bool(user.is_superuser or user.role in (User.Role.LAB_STAFF, User.Role.ADMIN))
        return True

    def has_object_permission(self, request, view, obj):
        test = obj.lab_test
        return _check_lab_access(request.user, test.patient, test.requested_by, request.method)
