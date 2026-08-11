from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User


class IsAdminOrOwnerDoctorOrReadOnly(BasePermission):
    """Anyone authenticated can read. Admin can write anything. A doctor can write only their own record.

    On create there is no object yet for has_object_permission to check, so ownership of a new
    DoctorAvailability/DoctorLeave/Doctor row is enforced here: a non-admin doctor may only create a row
    whose `doctor` field points at their own Doctor profile.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS or view.action != "create":
            return True
        if user.is_superuser or user.role == User.Role.ADMIN:
            return True
        if user.role != User.Role.DOCTOR:
            return False
        from .models import Doctor

        own_doctor = Doctor.objects.filter(user=user).first()
        return bool(own_doctor) and str(request.data.get("doctor")) == str(own_doctor.id)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return True
        doctor = obj if hasattr(obj, "user") and obj.__class__.__name__ == "Doctor" else getattr(obj, "doctor", None)
        return bool(doctor and doctor.user_id == request.user.id)
