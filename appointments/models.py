from django.conf import settings
from django.db import models

from doctors.models import Doctor
from patients.models import Patient


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        IN_CONSULTATION = "in_consultation", "In Consultation"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    appointment_date = models.DateField()
    slot_start_time = models.TimeField()
    slot_end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reason = models.TextField(blank=True)
    token_number = models.CharField(max_length=20, blank=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    consultation_started_at = models.DateTimeField(null=True, blank=True)
    consultation_completed_at = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="booked_appointments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-appointment_date", "slot_start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "appointment_date", "slot_start_time"],
                condition=~models.Q(status="cancelled"),
                name="unique_active_slot_per_doctor",
            )
        ]

    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.appointment_date} {self.slot_start_time}"


class Waitlist(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        NOTIFIED = "notified", "Notified"
        BOOKED = "booked", "Booked"
        CANCELLED = "cancelled", "Cancelled"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="waitlist_entries")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="waitlist_entries")
    preferred_date = models.DateField(help_text="The date the patient wants a slot to open up on.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.patient} waiting for {self.doctor} on {self.preferred_date} ({self.status})"


class Feedback(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="feedback")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="feedback_given")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="feedback_received")
    rating = models.PositiveSmallIntegerField(help_text="1 (poor) to 5 (excellent)")
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(rating__gte=1) & models.Q(rating__lte=5), name="feedback_rating_range"),
        ]

    def __str__(self):
        return f"{self.rating}/5 from {self.patient} for {self.doctor}"
