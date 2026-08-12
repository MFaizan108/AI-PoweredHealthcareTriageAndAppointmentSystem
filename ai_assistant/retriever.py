"""Retriever half of the RAG pipeline: User -> Permission Check -> Retriever ->
Patient's authorized records / hospital FAQs -> LLM -> Response.

Only ever reads data already scoped to the requesting patient — never another patient's records.
"""

from django.utils import timezone

from .models import HospitalFAQ


def get_patient_context(patient):
    lines = []

    upcoming = (
        patient.appointments.exclude(status__in=["cancelled", "completed"])
        .filter(appointment_date__gte=timezone.localdate())
        .order_by("appointment_date", "slot_start_time")[:3]
    )
    if upcoming:
        lines.append("Upcoming appointments:")
        for a in upcoming:
            lines.append(f"- {a.appointment_date} {a.slot_start_time} with {a.doctor} ({a.status}), token {a.token_number}")
    else:
        lines.append("Upcoming appointments: none scheduled.")

    prescriptions = patient.prescriptions.order_by("-created_at")[:2]
    if prescriptions:
        lines.append("Recent prescriptions:")
        for p in prescriptions:
            meds = ", ".join(item.medicine_name for item in p.items.all()) or "(no items listed)"
            lines.append(f"- {p.created_at.date()} by {p.doctor}: {meds}")

    lab_tests = patient.lab_tests.order_by("-requested_at")[:2]
    if lab_tests:
        lines.append("Recent lab tests:")
        for t in lab_tests:
            lines.append(f"- {t.test_name}: {t.status}")

    return "\n".join(lines)


def search_faqs(query, limit=3):
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    if not query_words:
        return []

    matches = []
    for faq in HospitalFAQ.objects.filter(is_active=True):
        haystack = f"{faq.question} {faq.answer}".lower()
        score = sum(1 for w in query_words if w in haystack)
        if score:
            matches.append((score, faq))

    matches.sort(key=lambda pair: pair[0], reverse=True)
    return [faq for _, faq in matches[:limit]]
