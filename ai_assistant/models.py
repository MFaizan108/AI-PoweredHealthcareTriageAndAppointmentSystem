from django.conf import settings
from django.db import models


class HospitalFAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Hospital FAQ"
        verbose_name_plural = "Hospital FAQs"
        ordering = ["id"]

    def __str__(self):
        return self.question


class AssistantQueryLog(models.Model):
    """Kept for basic audit/debugging of what the assistant retrieved and answered."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assistant_queries")
    message = models.TextField()
    retrieved_context = models.TextField(blank=True)
    response = models.TextField(blank=True)
    provider_used = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
