from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from patients.models import Patient
from triage.llm import ask_llm
from triage.throttles import AIRateThrottle

from .models import AssistantQueryLog, HospitalFAQ
from .permissions import IsAdminOrReadOnlyForAuthenticated
from .retriever import get_patient_context, search_faqs
from .serializers import AskSerializer, AssistantQueryLogSerializer, HospitalFAQSerializer


class AskResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
    provider_used = serializers.CharField(allow_blank=True)
    error = serializers.CharField(allow_blank=True)


SYSTEM_PROMPT = (
    "You are a helpful hospital patient assistant. Answer ONLY using the CONTEXT provided below "
    "(the patient's own appointments/prescriptions/lab tests and relevant hospital FAQs). "
    "If the answer is not in the context, say you don't have that information and suggest contacting "
    "the reception desk. Do NOT diagnose, do NOT give medical advice beyond what's in the context, "
    "and keep answers short and clear."
)


@extend_schema(
    tags=["AI Assistant"],
    request=AskSerializer,
    responses=AskResponseSerializer,
    description=(
        "RAG pipeline: permission check (patient may only query their own data) -> retriever "
        "(patient's own appointments/prescriptions/lab tests + matching hospital FAQs) -> LLM -> response. "
        "Never bypasses per-patient authorization, even if the question references another patient."
    ),
)
class AssistantAskView(APIView):
    """User -> Permission Check -> Retriever -> Patient's authorized records / hospital FAQs -> LLM -> Response."""

    permission_classes = [IsAuthenticated]
    # Every call triggers a real LLM request — see triage.throttles.AIRateThrottle. Both
    # throttle_classes and throttle_scope are required (ScopedRateThrottle reads view.throttle_scope).
    throttle_classes = [AIRateThrottle]
    throttle_scope = "ai"

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]

        # Permission check: only a patient may query their own authorized data.
        if request.user.role != User.Role.PATIENT and not request.user.is_superuser:
            return Response({"detail": "Only patients can use this assistant."}, status=403)
        patient = get_object_or_404(Patient, user=request.user)

        # Retriever: scoped strictly to this patient + the public FAQ set.
        patient_context = get_patient_context(patient)
        faqs = search_faqs(message)
        faq_context = "\n".join(f"Q: {f.question}\nA: {f.answer}" for f in faqs)

        context = f"PATIENT DATA:\n{patient_context}\n\nHOSPITAL FAQs:\n{faq_context or '(none matched)'}"
        prompt = f"CONTEXT:\n{context}\n\nPATIENT QUESTION: {message}"

        # LLM
        response_text, provider_used, error = ask_llm(SYSTEM_PROMPT, prompt)
        if response_text is None:
            response_text = "Sorry, the assistant is temporarily unavailable. Please contact the reception desk for help."

        AssistantQueryLog.objects.create(
            user=request.user,
            message=message,
            retrieved_context=context,
            response=response_text,
            provider_used=provider_used or "",
        )

        return Response({"response": response_text, "provider_used": provider_used or "", "error": error or ""})


@extend_schema_view(
    list=extend_schema(tags=["AI Assistant"]),
    retrieve=extend_schema(tags=["AI Assistant"]),
    create=extend_schema(tags=["AI Assistant"]),
    update=extend_schema(tags=["AI Assistant"]),
    partial_update=extend_schema(tags=["AI Assistant"]),
    destroy=extend_schema(tags=["AI Assistant"]),
)
class HospitalFAQViewSet(viewsets.ModelViewSet):
    """Admin manages FAQ content; any authenticated user can read it. Used as retrieval context for the assistant."""

    queryset = HospitalFAQ.objects.filter(is_active=True)
    serializer_class = HospitalFAQSerializer
    permission_classes = [IsAdminOrReadOnlyForAuthenticated]


@extend_schema_view(list=extend_schema(tags=["AI Assistant"], description="The current user's own AI-assistant query history."))
class AssistantHistoryView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AssistantQueryLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AssistantQueryLog.objects.filter(user=self.request.user)
