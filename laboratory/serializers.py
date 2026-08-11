from rest_framework import serializers

from doctors.serializers import DoctorSerializer
from patients.serializers import PatientSerializer

from .models import LabReport, LabTest


class LabReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabReport
        fields = [
            "id", "lab_test", "report_file", "result_summary", "uploaded_by",
            "uploaded_at", "reviewed_by_doctor", "reviewed_at",
        ]
        read_only_fields = ["id", "uploaded_by", "uploaded_at"]


class LabTestSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    requested_by_detail = DoctorSerializer(source="requested_by", read_only=True)
    report = LabReportSerializer(read_only=True)

    class Meta:
        model = LabTest
        fields = [
            "id", "patient", "patient_detail", "requested_by", "requested_by_detail", "appointment",
            "test_name", "notes", "status", "report", "requested_at", "updated_at",
        ]
        read_only_fields = ["id", "requested_at", "updated_at"]
