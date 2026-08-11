from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from accounts.models import User
from doctors.models import Doctor
from notifications.models import Notification
from notifications.services import notify

from .models import Prescription, PrescriptionItem
from .pdf import render_prescription_pdf
from .permissions import (
    IsOwnerPatientOrPrescribingDoctorOrAdmin,
    IsOwnerPatientOrPrescribingDoctorOrAdminViaPrescription,
)
from .serializers import PrescriptionItemSerializer, PrescriptionSerializer


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.select_related("patient__user", "doctor__user").prefetch_related("items")
    serializer_class = PrescriptionSerializer
    permission_classes = [IsOwnerPatientOrPrescribingDoctorOrAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            pass  # unrestricted
        elif user.role == User.Role.PATIENT:
            qs = qs.filter(patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(doctor__user=user)
        else:
            return qs.none()
        patient = self.request.query_params.get("patient")
        if patient:
            qs = qs.filter(patient_id=patient)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.DOCTOR:
            doctor = Doctor.objects.filter(user=user).first()
            if not doctor:
                raise ValidationError("No doctor profile found for this user.")
            prescription = serializer.save(doctor=doctor)
        else:
            prescription = serializer.save()

        notify(
            prescription.patient.user,
            Notification.NotificationType.PRESCRIPTION_AVAILABLE,
            "New Prescription Available",
            f"Dr. {prescription.doctor} has issued a new prescription for you.",
        )

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        prescription = self.get_object()
        buffer = render_prescription_pdf(prescription)
        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="prescription_{prescription.id}.pdf"'
        return response


class PrescriptionItemViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionItem.objects.select_related("prescription")
    serializer_class = PrescriptionItemSerializer
    permission_classes = [IsOwnerPatientOrPrescribingDoctorOrAdminViaPrescription]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            return qs
        if user.role == User.Role.PATIENT:
            return qs.filter(prescription__patient__user=user)
        if user.role == User.Role.DOCTOR:
            return qs.filter(prescription__doctor__user=user)
        return qs.none()
