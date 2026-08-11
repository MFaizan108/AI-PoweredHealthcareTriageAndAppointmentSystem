from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from accounts.models import User
from doctors.models import Doctor

from .models import Diagnosis, MedicalRecord
from .permissions import (
    IsOwnerPatientOrTreatingDoctorOrAdmin,
    IsOwnerPatientOrTreatingDoctorOrAdminViaMedicalRecord,
)
from .serializers import DiagnosisSerializer, MedicalRecordSerializer


class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.select_related("patient__user", "doctor__user")
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsOwnerPatientOrTreatingDoctorOrAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.PATIENT:
            qs = qs.filter(patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(doctor__user=user)
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
            serializer.save(doctor=doctor)
        else:
            serializer.save()


class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.select_related("medical_record")
    serializer_class = DiagnosisSerializer
    permission_classes = [IsOwnerPatientOrTreatingDoctorOrAdminViaMedicalRecord]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.PATIENT:
            qs = qs.filter(medical_record__patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(medical_record__doctor__user=user)
        return qs
