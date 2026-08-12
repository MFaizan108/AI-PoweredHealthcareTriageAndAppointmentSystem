from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from ai_healthcare_triage_appointment_system.validators import MaxFileSizeValidator
from appointments.models import Appointment

ALLOWED_ATTACHMENT_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "doc", "docx"]


class Message(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages")
    body = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="message_attachments/%Y/%m/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(ALLOWED_ATTACHMENT_EXTENSIONS), MaxFileSizeValidator(10)],
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} -> {self.recipient} ({self.appointment_id})"
