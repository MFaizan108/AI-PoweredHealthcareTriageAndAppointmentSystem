from rest_framework import serializers

from doctors.serializers import DoctorSerializer
from patients.serializers import PatientSerializer

from .models import Diagnosis, MedicalRecord


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = ["id", "medical_record", "description", "diagnosed_at"]
        read_only_fields = ["id", "diagnosed_at"]


class MedicalRecordSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    doctor_detail = DoctorSerializer(source="doctor", read_only=True)
    diagnoses = DiagnosisSerializer(many=True, read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            "id", "patient", "patient_detail", "doctor", "doctor_detail", "appointment",
            "visit_date", "consultation_notes", "follow_up_date", "follow_up_notes",
            "diagnoses", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
