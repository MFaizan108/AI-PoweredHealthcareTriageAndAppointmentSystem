from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User

BILLING_STAFF = {User.Role.ADMIN, User.Role.RECEPTIONIST}


class CanAccessInvoice(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(user.is_superuser or user.role in BILLING_STAFF)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role in BILLING_STAFF:
            return True
        if user.role == User.Role.PATIENT:
            return obj.patient.user_id == user.id and request.method in SAFE_METHODS
        return False


class CanAccessPayment(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(user.is_superuser or user.role in BILLING_STAFF)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role in BILLING_STAFF:
            return True
        if user.role == User.Role.PATIENT:
            return obj.invoice.patient.user_id == user.id and request.method in SAFE_METHODS
        return False
