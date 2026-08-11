from rest_framework.permissions import BasePermission

from accounts.models import User

BOOKING_ROLES = {User.Role.PATIENT, User.Role.RECEPTIONIST, User.Role.ADMIN}


class CanManageAppointment(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if view.action == "create":
            return user.is_superuser or user.role in BOOKING_ROLES
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role in (User.Role.ADMIN, User.Role.RECEPTIONIST):
            return True
        if user.role == User.Role.PATIENT:
            return obj.patient.user_id == user.id
        if user.role == User.Role.DOCTOR:
            return obj.doctor.user_id == user.id
        return False
