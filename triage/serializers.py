from rest_framework import serializers

from departments.serializers import DepartmentSerializer
from patients.models import Patient
from patients.serializers import PatientSerializer

from .models import AIProviderSettings, EmergencyGuidance, Symptom, TriageAssessment


class AIProviderSettingsSerializer(serializers.ModelSerializer):
    groq_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    groq_api_key_set = serializers.SerializerMethodField()

    class Meta:
        model = AIProviderSettings
        fields = [
            "id", "is_enabled", "provider", "ollama_base_url", "ollama_model",
            "groq_api_key", "groq_api_key_set", "groq_model", "timeout_seconds", "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]

    def get_groq_api_key_set(self, obj) -> bool:
        return bool(obj.groq_api_key)


class SymptomSerializer(serializers.ModelSerializer):
    suggested_department_name = serializers.CharField(source="suggested_department.name", read_only=True)

    class Meta:
        model = Symptom
        fields = [
            "id", "name", "category", "keywords", "severity_weight", "red_flag",
            "suggested_department", "suggested_department_name",
        ]
        read_only_fields = ["id"]


class TriageAssessmentSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    detected_symptoms = SymptomSerializer(many=True, read_only=True)
    suggested_department_detail = DepartmentSerializer(source="suggested_department", read_only=True)
    disclaimer = serializers.SerializerMethodField()

    class Meta:
        model = TriageAssessment
        fields = [
            "id", "patient", "patient_detail", "appointment", "symptoms_text", "detected_symptoms",
            "urgency", "suggested_department", "suggested_department_detail", "reasoning",
            "ai_summary", "ai_provider_used", "ai_summary_error", "disclaimer",
            "reviewed_by", "clinician_agrees", "clinician_notes", "reviewed_at", "created_at",
        ]
        read_only_fields = [
            "id", "detected_symptoms", "urgency", "suggested_department", "reasoning",
            "ai_summary", "ai_provider_used", "ai_summary_error",
            "reviewed_by", "clinician_agrees", "clinician_notes", "reviewed_at", "created_at",
        ]

    def get_disclaimer(self, obj) -> str:
        return TriageAssessment.DISCLAIMER


class TriageReviewSerializer(serializers.Serializer):
    clinician_agrees = serializers.BooleanField()
    clinician_notes = serializers.CharField(required=False, allow_blank=True)


class EmergencyGuidanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyGuidance
        fields = ["id", "urgency", "title", "content", "emergency_numbers"]
        read_only_fields = ["id"]


class TriageRequestSerializer(serializers.Serializer):
    """Input payload for POST /api/triage/assess/."""

    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all(), required=False)
    appointment = serializers.IntegerField(required=False, allow_null=True)
    symptoms_text = serializers.CharField()
    use_ai_summary = serializers.BooleanField(required=False, default=True)
