from django.db import models

from appointments.models import Appointment
from departments.models import Department
from patients.models import Patient

from .crypto import decrypt_value, encrypt_value


class AIProviderSettings(models.Model):
    """Singleton config, editable from Django admin, controlling which LLM the
    Layer-3 symptom summarizer uses. The rule-based Layer 1 engine never depends
    on this — if the LLM is disabled or unreachable, triage still works."""

    class Provider(models.TextChoices):
        OLLAMA = "ollama", "Ollama (Local)"
        GROQ = "groq", "Groq (Cloud)"

    is_enabled = models.BooleanField(
        default=True, help_text="If off, triage skips the LLM summary and returns only the rule-based result."
    )
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.OLLAMA)

    ollama_base_url = models.CharField(max_length=255, default="http://127.0.0.1:11434")
    ollama_model = models.CharField(max_length=100, default="qwen2.5:7b")

    groq_api_key_encrypted = models.TextField(
        blank=True, help_text="Encrypted at rest (Fernet, key derived from DJANGO_SECRET_KEY)."
    )
    groq_model = models.CharField(max_length=100, default="llama-3.1-8b-instant")

    timeout_seconds = models.PositiveIntegerField(default=60)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Provider Settings"
        verbose_name_plural = "AI Provider Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton — never actually deleted

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"AI Provider Settings ({self.get_provider_display()})"

    @property
    def groq_api_key(self):
        return decrypt_value(self.groq_api_key_encrypted)

    @groq_api_key.setter
    def groq_api_key(self, value):
        self.groq_api_key_encrypted = encrypt_value(value)


class Symptom(models.Model):
    class Category(models.TextChoices):
        GENERAL = "general", "General"
        RESPIRATORY = "respiratory", "Respiratory"
        CARDIAC = "cardiac", "Cardiac"
        NEUROLOGICAL = "neurological", "Neurological"
        GASTROINTESTINAL = "gastrointestinal", "Gastrointestinal"
        DERMATOLOGICAL = "dermatological", "Dermatological"
        DENTAL = "dental", "Dental"
        OPHTHALMOLOGICAL = "ophthalmological", "Ophthalmological"
        MUSCULOSKELETAL = "musculoskeletal", "Musculoskeletal"
        MENTAL_HEALTH = "mental_health", "Mental Health"
        ENT = "ent", "Ear/Nose/Throat"
        GYNECOLOGICAL = "gynecological", "Gynecological"

    name = models.CharField(max_length=150, unique=True)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.GENERAL)
    keywords = models.CharField(max_length=500, help_text="Comma-separated synonyms/phrases used for matching.")
    severity_weight = models.PositiveIntegerField(default=1, help_text="1 (mild) - 5 (severe) contribution to the urgency score.")
    red_flag = models.BooleanField(default=False, help_text="If matched, triage is escalated straight to Emergency.")
    suggested_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="symptoms"
    )

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class TriageAssessment(models.Model):
    class Urgency(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"
        EMERGENCY = "emergency", "Emergency"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="triage_assessments")
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="triage_assessments"
    )
    symptoms_text = models.TextField()
    detected_symptoms = models.ManyToManyField(Symptom, blank=True, related_name="assessments")
    urgency = models.CharField(max_length=20, choices=Urgency.choices)
    suggested_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="triage_assessments"
    )
    reasoning = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    ai_provider_used = models.CharField(max_length=20, blank=True)
    ai_summary_error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Clinician review — lets a doctor record whether they agreed with the AI's urgency,
    # for the "AI vs clinician agreement" monitoring metric. Never affects the triage result itself.
    reviewed_by = models.ForeignKey(
        "doctors.Doctor", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_assessments"
    )
    clinician_agrees = models.BooleanField(null=True, blank=True)
    clinician_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    DISCLAIMER = (
        "This is an AI-assisted preliminary triage, not a medical diagnosis. "
        "It does not replace evaluation by a qualified healthcare professional. "
        "If this is a medical emergency, seek immediate emergency care."
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Triage for {self.patient} - {self.urgency}"


class EmergencyGuidance(models.Model):
    """Admin-editable static guidance shown alongside HIGH/EMERGENCY triage results."""

    urgency = models.CharField(max_length=20, choices=TriageAssessment.Urgency.choices, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    emergency_numbers = models.CharField(max_length=255, blank=True, help_text="e.g. 'Pakistan: 1122 (Rescue), 15 (Police)'")

    class Meta:
        verbose_name_plural = "Emergency guidance"
        ordering = ["urgency"]

    def __str__(self):
        return f"Guidance for {self.urgency}"
