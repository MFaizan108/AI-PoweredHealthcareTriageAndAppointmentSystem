from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        APPOINTMENT_BOOKED = "appointment_booked", "Appointment Booked"
        APPOINTMENT_REMINDER = "appointment_reminder", "Appointment Reminder"
        APPOINTMENT_CANCELLED = "appointment_cancelled", "Appointment Cancelled"
        LAB_REPORT_AVAILABLE = "lab_report_available", "Lab Report Available"
        PRESCRIPTION_AVAILABLE = "prescription_available", "Prescription Available"
        FOLLOW_UP_REMINDER = "follow_up_reminder", "Follow-up Reminder"
        GENERAL = "general", "General"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.GENERAL)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification_type} -> {self.recipient}"
