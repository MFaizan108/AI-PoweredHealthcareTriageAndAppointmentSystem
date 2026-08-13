from django.urls import reverse
from rest_framework import serializers

from doctors.serializers import DoctorSerializer
from patients.serializers import PatientSerializer

from .models import LabReport, LabTest


class LabReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabReport
        fields = [
            "id",
            "lab_test",
            "report_file",
            "result_summary",
            "uploaded_by",
            "uploaded_at",
            "reviewed_by_doctor",
            "reviewed_at",
        ]
        read_only_fields = ["id", "uploaded_by", "uploaded_at"]

    def to_representation(self, instance):
        # `report_file` is writable (the upload field, handled above by the model field as usual) but
        # read back as the authenticated download endpoint's path, not the raw MEDIA_URL — nginx/Django
        # serve /media/ with no permission check at all, so the raw path would make the file reachable
        # by anyone who ever sees this response, forever. A relative path (not build_absolute_uri) to
        # match every other URL in this API, which all resolve correctly under both the Vite dev proxy
        # and the production nginx proxy without a build-time base-URL switch — see docs/frontend.md.
        data = super().to_representation(instance)
        data["report_file"] = reverse("lab-report-download", kwargs={"pk": instance.pk}) if instance.report_file else None
        return data


class LabTestSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    requested_by_detail = DoctorSerializer(source="requested_by", read_only=True)
    report = LabReportSerializer(read_only=True)

    class Meta:
        model = LabTest
        fields = [
            "id",
            "patient",
            "patient_detail",
            "requested_by",
            "requested_by_detail",
            "appointment",
            "test_name",
            "notes",
            "status",
            "report",
            "requested_at",
            "updated_at",
        ]
        read_only_fields = ["id", "requested_at", "updated_at"]
