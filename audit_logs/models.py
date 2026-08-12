from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCESS = "login_success", "Login Success"
        LOGIN_FAILED = "login_failed", "Login Failed"
        LOGOUT = "logout", "Logout"
        REQUEST = "request", "API Request"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    username_attempted = models.CharField(max_length=150, blank=True, help_text="Set for failed logins where no user object is available.")
    action = models.CharField(max_length=20, choices=Action.choices, default=Action.REQUEST)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=500, blank=True)
    object_id = models.CharField(
        max_length=50, blank=True,
        help_text="Best-effort — the trailing numeric ID in the URL path (e.g. '42' for /api/appointments/42/).",
    )
    changes = models.JSONField(
        default=dict, blank=True,
        help_text="The submitted request body for this mutation, with sensitive fields "
        "(password/token/otp_code/api keys/...) redacted. Captures intent, not a computed diff.",
    )
    status_code = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, help_text="Raw User-Agent header — used for login/device history.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):
        who = self.user or self.username_attempted or "anonymous"
        return f"[{self.action}] {who} {self.method} {self.path} ({self.status_code})"
