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


class IsOwnerPatientOrTreatingDoctorOrAdmin(BasePermission):
    """Patient can read their own record. Doctor can read/write records they authored.
    Admin has full access. Receptionist and lab staff are excluded (clinical data)."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if view.action == "create":
            return bool(user.is_superuser or user.role in (User.Role.DOCTOR, User.Role.ADMIN))
        return True

    def has_object_permission(self, request, view, obj):
        return _check_clinical_access(request.user, obj.patient, obj.doctor, request.method)


class IsOwnerPatientOrTreatingDoctorOrAdminViaMedicalRecord(IsOwnerPatientOrTreatingDoctorOrAdmin):
    """Same rule as above, but the object is a child of MedicalRecord (e.g. Diagnosis)."""

    def has_object_permission(self, request, view, obj):
        record = obj.medical_record
        return _check_clinical_access(request.user, record.patient, record.doctor, request.method)
