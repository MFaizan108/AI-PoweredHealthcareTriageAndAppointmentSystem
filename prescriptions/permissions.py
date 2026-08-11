from rest_framework.permissions import BasePermission

from accounts.models import User


def _check_clinical_access(user, patient, doctor, method):
    if user.is_superuser or user.role == User.Role.ADMIN:
        return True
    if user.role == User.Role.PATIENT:
        return patient.user_id == user.id and method in ("GET", "HEAD", "OPTIONS")
    if user.role == User.Role.DOCTOR:
        return bool(doctor and doctor.user_id == user.id)
    return False


class IsOwnerPatientOrPrescribingDoctorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if view.action == "create":
            return bool(user.is_superuser or user.role in (User.Role.DOCTOR, User.Role.ADMIN))
        return True

    def has_object_permission(self, request, view, obj):
        return _check_clinical_access(request.user, obj.patient, obj.doctor, request.method)


class IsOwnerPatientOrPrescribingDoctorOrAdminViaPrescription(IsOwnerPatientOrPrescribingDoctorOrAdmin):
    def has_object_permission(self, request, view, obj):
        prescription = obj.prescription
        return _check_clinical_access(request.user, prescription.patient, prescription.doctor, request.method)
