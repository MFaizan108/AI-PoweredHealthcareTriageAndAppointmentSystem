import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=15)
def generate_ai_summary_task(self, assessment_id):
    """Runs the Layer-3 LLM summary in the background so a slow/unreachable Ollama/Groq call never
    blocks the triage HTTP response — the rule-based urgency/department result is already saved and
    returned to the client before this task even starts."""
    from .llm import generate_ai_summary
    from .models import TriageAssessment

    try:
        assessment = TriageAssessment.objects.select_related("suggested_department").prefetch_related("detected_symptoms").get(pk=assessment_id)
    except TriageAssessment.DoesNotExist:
        return

    detected_names = [s.name for s in assessment.detected_symptoms.all()]
    summary, provider, error = generate_ai_summary(assessment.symptoms_text, detected_names, assessment.urgency)

    assessment.ai_summary = summary or ""
    assessment.ai_provider_used = provider or ""
    assessment.ai_summary_error = error or ""
    assessment.ai_summary_status = (
        TriageAssessment.AISummaryStatus.READY if summary else TriageAssessment.AISummaryStatus.FAILED
    )
    assessment.save(update_fields=["ai_summary", "ai_provider_used", "ai_summary_error", "ai_summary_status"])
