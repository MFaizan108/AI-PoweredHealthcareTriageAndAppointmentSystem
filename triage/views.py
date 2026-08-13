from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from appointments.models import Appointment
from doctors.models import Doctor
from patients.models import Patient

from .models import AIProviderSettings, EmergencyGuidance, Symptom, TriageAssessment
from .permissions import CanAccessTriageAssessment, IsAdminOnly, IsAdminOrReadOnlyForAuthenticated
from .rules_engine import run_rule_based_triage
from .serializers import (
    AIProviderSettingsSerializer,
    EmergencyGuidanceSerializer,
    SymptomSerializer,
    TriageAssessmentSerializer,
    TriageRequestSerializer,
    TriageReviewSerializer,
)
from .tasks import generate_ai_summary_task
from .throttles import AIRateThrottle


@extend_schema_view(
    get=extend_schema(
        tags=["Triage"], responses=AIProviderSettingsSerializer, description="View the current LLM provider configuration."
    ),
    patch=extend_schema(
        tags=["Triage"],
        request=AIProviderSettingsSerializer,
        responses=AIProviderSettingsSerializer,
        description="Update the LLM provider (Ollama/Groq), model, and Groq API key (encrypted at rest).",
    ),
)
class AIProviderSettingsView(APIView):
    """Admin-only: view/update which LLM backend (Ollama or Groq) triage summaries use."""

    permission_classes = [IsAdminOnly]

    def get(self, request):
        obj = AIProviderSettings.get_solo()
        return Response(AIProviderSettingsSerializer(obj).data)

    def patch(self, request):
        obj = AIProviderSettings.get_solo()
        serializer = AIProviderSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AIProviderSettingsSerializer(obj).data)


@extend_schema_view(
    list=extend_schema(tags=["Triage"]),
    retrieve=extend_schema(tags=["Triage"]),
    create=extend_schema(tags=["Triage"]),
    update=extend_schema(tags=["Triage"]),
    partial_update=extend_schema(tags=["Triage"]),
    destroy=extend_schema(tags=["Triage"]),
)
class SymptomViewSet(viewsets.ModelViewSet):
    """Admin-managed catalog of symptoms used by the rule-based triage engine (Layer 1)."""

    queryset = Symptom.objects.select_related("suggested_department")
    serializer_class = SymptomSerializer
    permission_classes = [IsAdminOrReadOnlyForAuthenticated]


@extend_schema_view(
    list=extend_schema(
        tags=["Triage"],
        description="List past triage assessments visible to the requesting user (own, for patients; own patients', for doctors; all, for admins).",
    ),
    retrieve=extend_schema(tags=["Triage"]),
)
class TriageAssessmentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only listing of past assessments. Creation goes through TriageAssessView below,
    since it runs the rule engine + LLM rather than a plain model create."""

    queryset = TriageAssessment.objects.select_related("patient__user", "suggested_department").prefetch_related(
        "detected_symptoms"
    )
    serializer_class = TriageAssessmentSerializer
    permission_classes = [CanAccessTriageAssessment]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            pass  # unrestricted
        elif user.role == User.Role.PATIENT:
            qs = qs.filter(patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(appointment__doctor__user=user)
        else:
            # Receptionist may create an assessment on a patient's behalf but cannot browse them afterwards.
            return qs.none()
        patient = self.request.query_params.get("patient")
        if patient:
            qs = qs.filter(patient_id=patient)
        return qs

    @extend_schema(
        tags=["Triage"],
        request=TriageReviewSerializer,
        description="A doctor/admin records whether they agreed with the AI's urgency call (for analytics only — does not alter the stored urgency).",
    )
    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """A doctor records whether they agreed with the AI's urgency call (for analytics only)."""
        assessment = self.get_object()
        user = request.user
        if not (user.is_superuser or user.role in (User.Role.DOCTOR, User.Role.ADMIN)):
            return Response({"detail": "Only doctors/admins can review a triage assessment."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TriageReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doctor = Doctor.objects.filter(user=user).first()
        assessment.reviewed_by = doctor
        assessment.clinician_agrees = serializer.validated_data["clinician_agrees"]
        assessment.clinician_notes = serializer.validated_data.get("clinician_notes", "")
        assessment.reviewed_at = timezone.now()
        assessment.save(update_fields=["reviewed_by", "clinician_agrees", "clinician_notes", "reviewed_at"])
        return Response(TriageAssessmentSerializer(assessment).data)


@extend_schema_view(
    list=extend_schema(tags=["Triage"]),
    retrieve=extend_schema(tags=["Triage"]),
    create=extend_schema(tags=["Triage"]),
    update=extend_schema(tags=["Triage"]),
    partial_update=extend_schema(tags=["Triage"]),
    destroy=extend_schema(tags=["Triage"]),
)
class EmergencyGuidanceViewSet(viewsets.ModelViewSet):
    """Admin manages content; any authenticated user can read it (surfaced after a HIGH/EMERGENCY triage result)."""

    queryset = EmergencyGuidance.objects.all()
    serializer_class = EmergencyGuidanceSerializer
    permission_classes = [IsAdminOrReadOnlyForAuthenticated]


@extend_schema(
    tags=["Triage"],
    request=TriageRequestSerializer,
    responses={201: TriageAssessmentSerializer},
    description=(
        "Runs Layer 1 (rule-based symptom matching + urgency scoring) and, if requested, Layer 3 "
        "(LLM-generated plain-language summary), then persists and returns the result. "
        "This is a preliminary triage / decision-support output only — not a medical diagnosis."
    ),
)
class TriageAssessView(APIView):
    """POST /api/triage/assess/ — run Layer 1 (rules) + Layer 3 (LLM summary) and persist the result."""

    permission_classes = [CanAccessTriageAssessment]
    # Stricter than the generic per-user rate — every call here can trigger a real LLM request
    # (default use_ai_summary=True). Applies uniformly rather than only when AI is actually
    # requested, trading a little strictness for a throttle that can't be fooled by a malformed
    # or unparseable request body. ScopedRateThrottle reads `view.throttle_scope`, not anything on
    # the throttle class itself — both must be set (see accounts.views.LoginView for the same pattern).
    throttle_classes = [AIRateThrottle]
    throttle_scope = "ai"

    def post(self, request):
        payload = TriageRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        user = request.user
        if user.role == User.Role.PATIENT:
            patient = get_object_or_404(Patient, user=user)
        else:
            patient = data.get("patient")
            if not patient:
                return Response({"patient": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

        appointment = None
        if data.get("appointment"):
            appointment = get_object_or_404(Appointment, pk=data["appointment"])
            if appointment.patient_id != patient.id:
                raise PermissionDenied("Appointment does not belong to this patient.")

        symptoms_text = data["symptoms_text"]

        matched_symptoms, urgency, department, reasoning = run_rule_based_triage(symptoms_text)

        want_ai_summary = data.get("use_ai_summary", True)
        assessment = TriageAssessment.objects.create(
            patient=patient,
            appointment=appointment,
            symptoms_text=symptoms_text,
            urgency=urgency,
            suggested_department=department,
            reasoning=reasoning,
            ai_summary_status=(
                TriageAssessment.AISummaryStatus.PENDING if want_ai_summary else TriageAssessment.AISummaryStatus.NOT_REQUESTED
            ),
        )
        assessment.detected_symptoms.set(matched_symptoms)

        if want_ai_summary:
            # Rule-based urgency/department is already saved and about to be returned — the LLM summary
            # runs in the background (see triage/tasks.py) so a slow/unreachable LLM never blocks this
            # response. In tests (CELERY_TASK_ALWAYS_EAGER=True) this runs synchronously before .delay()
            # returns, so refreshing below already picks up the finished result.
            generate_ai_summary_task.delay(assessment.id)
            assessment.refresh_from_db()

        return Response(TriageAssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)
