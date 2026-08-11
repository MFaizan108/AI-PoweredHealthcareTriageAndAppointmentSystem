from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AIProviderSettingsView,
    EmergencyGuidanceViewSet,
    SymptomViewSet,
    TriageAssessmentViewSet,
    TriageAssessView,
)

router = DefaultRouter()
router.register("symptoms", SymptomViewSet, basename="symptom")
router.register("emergency-guidance", EmergencyGuidanceViewSet, basename="emergency-guidance")
router.register("assessments", TriageAssessmentViewSet, basename="triage-assessment")

urlpatterns = [
    path("assess/", TriageAssessView.as_view(), name="triage-assess"),
    path("ai-settings/", AIProviderSettingsView.as_view(), name="ai-provider-settings"),
] + router.urls
