from rest_framework.permissions import BasePermission

from accounts.models import User


class IsConversationParticipant(BasePermission):
    """Only the patient and the doctor of the linked appointment may read/send messages there."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            return True
        return user.id in (obj.sender_id, obj.recipient_id)


def is_appointment_participant(user, appointment):
    if user.role == User.Role.PATIENT:
        return appointment.patient.user_id == user.id
    if user.role == User.Role.DOCTOR:
        return appointment.doctor.user_id == user.id
    return user.is_superuser or user.role == User.Role.ADMIN
