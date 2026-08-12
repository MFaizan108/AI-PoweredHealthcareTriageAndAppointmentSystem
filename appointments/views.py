from datetime import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.models import User
from doctors.models import Doctor
from notifications.models import Notification
from notifications.services import notify
from patients.models import Patient

from .models import Appointment, Feedback, Waitlist
from .permissions import CanManageAppointment
from .serializers import AppointmentSerializer, AvailableSlotSerializer, FeedbackSerializer, WaitlistSerializer
from .services import get_available_slots


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related("patient__user", "doctor__user")
    serializer_class = AppointmentSerializer
    permission_classes = [CanManageAppointment]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.role == User.Role.PATIENT:
            qs = qs.filter(patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(doctor__user=user)
        elif not (user.is_superuser or user.role in (User.Role.ADMIN, User.Role.RECEPTIONIST)):
            # lab_staff (or any other role) has no business case for appointment visibility.
            return qs.none()
        # admin / receptionist / superuser: unrestricted

        for param, field in (("doctor", "doctor_id"), ("patient", "patient_id"), ("status", "status")):
            value = self.request.query_params.get(param)
            if value:
                qs = qs.filter(**{field: value})

        date = self.request.query_params.get("date")
        if date:
            qs = qs.filter(appointment_date=date)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.PATIENT:
            patient = get_object_or_404(Patient, user=user)
            appointment = serializer.save(patient=patient, booked_by=user)
        else:
            appointment = serializer.save(booked_by=user)

        notify(
            appointment.patient.user,
            Notification.NotificationType.APPOINTMENT_BOOKED,
            "Appointment Booked",
            (
                f"Your appointment with {appointment.doctor} on {appointment.appointment_date} "
                f"at {appointment.slot_start_time} is booked. Token: {appointment.token_number}."
            ),
        )

    @action(detail=False, methods=["get"], url_path="available-slots")
    def available_slots(self, request):
        doctor_id = request.query_params.get("doctor")
        date_str = request.query_params.get("date")
        if not doctor_id or not date_str:
            return Response({"detail": "doctor and date query params are required."}, status=status.HTTP_400_BAD_REQUEST)

        doctor = get_object_or_404(Doctor, pk=doctor_id)
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "date must be in YYYY-MM-DD format."}, status=status.HTTP_400_BAD_REQUEST)

        slots = get_available_slots(doctor, date)
        return Response(AvailableSlotSerializer(slots, many=True).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])

        notify(
            appointment.patient.user,
            Notification.NotificationType.APPOINTMENT_CANCELLED,
            "Appointment Cancelled",
            f"Your appointment with {appointment.doctor} on {appointment.appointment_date} at {appointment.slot_start_time} was cancelled.",
        )
        if appointment.doctor.user_id != request.user.id:
            notify(
                appointment.doctor.user,
                Notification.NotificationType.APPOINTMENT_CANCELLED,
                "Appointment Cancelled",
                f"Appointment with {appointment.patient} on {appointment.appointment_date} at {appointment.slot_start_time} was cancelled.",
            )

        # A slot just opened up — best-effort notify the first waiting patient for this doctor/date.
        next_in_line = (
            Waitlist.objects.filter(
                doctor=appointment.doctor, preferred_date=appointment.appointment_date, status=Waitlist.Status.WAITING
            )
            .order_by("created_at")
            .first()
        )
        if next_in_line:
            next_in_line.status = Waitlist.Status.NOTIFIED
            next_in_line.save(update_fields=["status"])
            notify(
                next_in_line.patient.user,
                Notification.NotificationType.GENERAL,
                "A slot opened up",
                f"A slot with {appointment.doctor} on {appointment.appointment_date} just opened up. Book quickly before it's taken.",
            )

        return Response(self.get_serializer(appointment).data)

    @action(detail=False, methods=["get"])
    def queue(self, request):
        """Receptionist/doctor token queue view for a given doctor + date."""
        doctor_id = request.query_params.get("doctor")
        date_str = request.query_params.get("date") or timezone.localdate().isoformat()
        qs = self.get_queryset().filter(appointment_date=date_str).exclude(status=Appointment.Status.CANCELLED)
        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)
        qs = qs.order_by("slot_start_time")
        data = [
            {
                "token_number": a.token_number,
                "patient": a.patient.user.get_full_name() or a.patient.user.username,
                "doctor": str(a.doctor),
                "slot_start_time": a.slot_start_time,
                "status": a.status,
                "checked_in": a.checked_in,
            }
            for a in qs
        ]
        return Response(data)

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request, pk=None):
        user = request.user
        if not (user.is_superuser or user.role in (User.Role.RECEPTIONIST, User.Role.ADMIN)):
            return Response({"detail": "Only receptionist/admin can check in patients."}, status=status.HTTP_403_FORBIDDEN)
        appointment = self.get_object()
        appointment.checked_in = True
        appointment.checked_in_at = timezone.now()
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save(update_fields=["checked_in", "checked_in_at", "status", "updated_at"])
        return Response(self.get_serializer(appointment).data)

    @action(detail=True, methods=["post"], url_path="set-status")
    def set_status(self, request, pk=None):
        appointment = self.get_object()
        new_status = request.data.get("status")
        if new_status not in Appointment.Status.values:
            raise serializers.ValidationError({"status": f"Must be one of {Appointment.Status.values}."})

        update_fields = ["status", "updated_at"]
        appointment.status = new_status
        if new_status == Appointment.Status.IN_CONSULTATION and not appointment.consultation_started_at:
            appointment.consultation_started_at = timezone.now()
            update_fields.append("consultation_started_at")
        elif new_status == Appointment.Status.COMPLETED and not appointment.consultation_completed_at:
            appointment.consultation_completed_at = timezone.now()
            update_fields.append("consultation_completed_at")

        appointment.save(update_fields=update_fields)
        return Response(self.get_serializer(appointment).data)


class WaitlistViewSet(viewsets.ModelViewSet):
    queryset = Waitlist.objects.select_related("patient__user", "doctor__user")
    serializer_class = WaitlistSerializer
    permission_classes = [CanManageAppointment]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.PATIENT:
            qs = qs.filter(patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(doctor__user=user)
        elif not (user.is_superuser or user.role in (User.Role.ADMIN, User.Role.RECEPTIONIST)):
            return qs.none()
        doctor = self.request.query_params.get("doctor")
        if doctor:
            qs = qs.filter(doctor_id=doctor)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.PATIENT:
            patient = get_object_or_404(Patient, user=user)
            serializer.save(patient=patient)
        else:
            serializer.save()

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        entry = self.get_object()
        entry.status = Waitlist.Status.CANCELLED
        entry.save(update_fields=["status"])
        return Response(self.get_serializer(entry).data)


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.select_related("patient__user", "doctor__user", "appointment")
    serializer_class = FeedbackSerializer
    permission_classes = [CanManageAppointment]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.PATIENT:
            qs = qs.filter(patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(doctor__user=user)
        elif not (user.is_superuser or user.role in (User.Role.ADMIN, User.Role.RECEPTIONIST)):
            return qs.none()
        doctor = self.request.query_params.get("doctor")
        if doctor:
            qs = qs.filter(doctor_id=doctor)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        appointment = serializer.validated_data["appointment"]
        if user.role != User.Role.PATIENT or appointment.patient.user_id != user.id:
            raise PermissionDenied("You can only leave feedback for your own completed appointments.")
        serializer.save(patient=appointment.patient, doctor=appointment.doctor)
