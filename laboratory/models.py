from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from ai_healthcare_triage_appointment_system.validators import MaxFileSizeValidator
from appointments.models import Appointment
from doctors.models import Doctor
from patients.models import Patient

ALLOWED_REPORT_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"]


class LabTest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        SAMPLE_COLLECTED = "sample_collected", "Sample Collected"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="lab_tests")
    requested_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name="requested_lab_tests")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="lab_tests")
    test_name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["status"], name="labtest_status_idx"),
        ]

    def __str__(self):
        return f"{self.test_name} for {self.patient} ({self.status})"


class LabReport(models.Model):
    lab_test = models.OneToOneField(LabTest, on_delete=models.CASCADE, related_name="report")
    report_file = models.FileField(
        upload_to="lab_reports/%Y/%m/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(ALLOWED_REPORT_EXTENSIONS), MaxFileSizeValidator(10)],
    )
    result_summary = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="uploaded_lab_reports"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_by_doctor = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Report for {self.lab_test}"
