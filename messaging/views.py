from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from appointments.models import Appointment

from .models import Message
from .permissions import IsConversationParticipant, is_appointment_participant
from .serializers import MessageSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.select_related("sender", "recipient", "appointment")
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsConversationParticipant]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user.is_superuser or user.role == User.Role.ADMIN):
            from django.db.models import Q

            qs = qs.filter(Q(sender=user) | Q(recipient=user))
        appointment = self.request.query_params.get("appointment")
        if appointment:
            qs = qs.filter(appointment_id=appointment)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        appointment_id = self.request.data.get("appointment")
        appointment = Appointment.objects.select_related("patient__user", "doctor__user").filter(pk=appointment_id).first()
        if not appointment:
            raise ValidationError({"appointment": "Not found."})
        if not is_appointment_participant(user, appointment):
            raise PermissionDenied("You are not a participant in this appointment's conversation.")

        recipient = appointment.doctor.user if user.id == appointment.patient.user_id else appointment.patient.user
        serializer.save(sender=user, recipient=recipient, appointment=appointment)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        message = self.get_object()
        if message.recipient_id != request.user.id:
            raise PermissionDenied("Only the recipient can mark a message as read.")
        message.is_read = True
        message.save(update_fields=["is_read"])
        return Response(self.get_serializer(message).data)
