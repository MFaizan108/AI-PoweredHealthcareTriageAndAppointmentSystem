from django import forms
from django.contrib import admin

from .models import AIProviderSettings, EmergencyGuidance, Symptom, TriageAssessment


class AIProviderSettingsForm(forms.ModelForm):
    groq_api_key = forms.CharField(
        required=False, widget=forms.PasswordInput(render_value=True),
        help_text="Stored encrypted at rest. Leave unchanged to keep the current key.",
    )

    class Meta:
        model = AIProviderSettings
        fields = ["is_enabled", "provider", "timeout_seconds", "ollama_base_url", "ollama_model", "groq_api_key", "groq_model"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["groq_api_key"].initial = self.instance.groq_api_key

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.groq_api_key = self.cleaned_data["groq_api_key"]
        if commit:
            instance.save()
        return instance


@admin.register(AIProviderSettings)
class AIProviderSettingsAdmin(admin.ModelAdmin):
    """Singleton config screen: pick Ollama vs Groq and paste the Groq API key here."""

    form = AIProviderSettingsForm
    list_display = ["provider", "is_enabled", "ollama_model", "groq_model", "updated_at"]
    fieldsets = (
        ("Switch", {"fields": ("is_enabled", "provider", "timeout_seconds")}),
        ("Ollama (Local)", {"fields": ("ollama_base_url", "ollama_model")}),
        ("Groq (Cloud)", {"fields": ("groq_api_key", "groq_model")}),
    )

    def has_add_permission(self, request):
        return not AIProviderSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = AIProviderSettings.get_solo()
        from django.shortcuts import redirect

        return redirect("admin:triage_aiprovidersettings_change", obj.pk)


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "severity_weight", "red_flag", "suggested_department"]
    list_filter = ["category", "red_flag", "suggested_department"]
    search_fields = ["name", "keywords"]


@admin.register(TriageAssessment)
class TriageAssessmentAdmin(admin.ModelAdmin):
    list_display = ["patient", "urgency", "suggested_department", "clinician_agrees", "ai_provider_used", "created_at"]
    list_filter = ["urgency", "ai_provider_used", "clinician_agrees"]
    search_fields = ["patient__user__username", "symptoms_text"]
    readonly_fields = [f.name for f in TriageAssessment._meta.fields]


@admin.register(EmergencyGuidance)
class EmergencyGuidanceAdmin(admin.ModelAdmin):
    list_display = ["urgency", "title"]
