from django.db import models

from appointments.models import Appointment
from doctors.models import Doctor
from patients.models import Patient


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_records")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name="medical_records")
    appointment = models.OneToOneField(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="medical_record"
    )
    visit_date = models.DateField()
    consultation_notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-visit_date", "-created_at"]

    def __str__(self):
        return f"Record for {self.patient} on {self.visit_date}"


class Diagnosis(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name="diagnoses")
    description = models.TextField()
    diagnosed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description[:60]
