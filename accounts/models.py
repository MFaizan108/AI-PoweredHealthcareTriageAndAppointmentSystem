from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        DOCTOR = "doctor", "Doctor"
        PATIENT = "patient", "Patient"
        RECEPTIONIST = "receptionist", "Receptionist"
        LAB_STAFF = "lab_staff", "Lab Staff"

    role = models.CharField(max_length=20, choices=Role.choices)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)

    otp_secret = models.CharField(max_length=64, blank=True)
    is_2fa_enabled = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f"{self.username} ({self.role})"


class TwoFactorRecoveryCode(models.Model):
    """One-time-use backup codes issued when 2FA is enabled — the recovery path when a user loses
    their authenticator device. Hashed at rest like a password; the plaintext is shown exactly once,
    in the response to POST /2fa/enable/ or /2fa/recovery-codes/regenerate/, and never again."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recovery_codes")
    code_hash = models.CharField(max_length=255)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "used_at"])]

    def __str__(self):
        return f"Recovery code for {self.user} ({'used' if self.used_at else 'unused'})"
