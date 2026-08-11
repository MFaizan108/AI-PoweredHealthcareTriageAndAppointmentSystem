from rest_framework.permissions import BasePermission

from .models import User


class IsRole(BasePermission):
    """Base permission: allows access only to users with a given role. Subclass and set `role`."""

    role = None

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == self.role or request.user.is_superuser)
        )


class IsAdmin(IsRole):
    role = User.Role.ADMIN


class IsDoctor(IsRole):
    role = User.Role.DOCTOR


class IsPatient(IsRole):
    role = User.Role.PATIENT


class IsReceptionist(IsRole):
    role = User.Role.RECEPTIONIST


class IsLabStaff(IsRole):
    role = User.Role.LAB_STAFF


class IsAdminOrReceptionist(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.role in (User.Role.ADMIN, User.Role.RECEPTIONIST)
                or request.user.is_superuser
            )
        )
