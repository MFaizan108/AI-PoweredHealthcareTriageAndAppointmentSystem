"""Layer 1 — Rule-Based Triage (deterministic safety layer).

symptom -> severity -> risk factors -> urgency

This layer is always authoritative. It never depends on the LLM (Layer 3) and
does not require a trained ML model (Layer 2 is left as a documented future
enhancement — see triage/README notes in the project blueprint).
"""
from collections import Counter

from .models import Symptom, TriageAssessment

HIGH_THRESHOLD = 8
MODERATE_THRESHOLD = 4


def match_symptoms(symptoms_text):
    text = symptoms_text.lower()
    matched = []
    for symptom in Symptom.objects.select_related("suggested_department").all():
        keywords = [k.strip().lower() for k in symptom.keywords.split(",") if k.strip()]
        if any(keyword in text for keyword in keywords):
            matched.append(symptom)
    return matched


def determine_urgency(matched_symptoms):
    if any(s.red_flag for s in matched_symptoms):
        return TriageAssessment.Urgency.EMERGENCY

    score = sum(s.severity_weight for s in matched_symptoms)
    if score >= HIGH_THRESHOLD:
        return TriageAssessment.Urgency.HIGH
    if score >= MODERATE_THRESHOLD:
        return TriageAssessment.Urgency.MODERATE
    return TriageAssessment.Urgency.LOW


def determine_department(matched_symptoms):
    departments = [s.suggested_department for s in matched_symptoms if s.suggested_department]
    if not departments:
        return None
    # Most red-flag/high-severity symptom's department wins ties by frequency first.
    red_flag_depts = [s.suggested_department for s in matched_symptoms if s.red_flag and s.suggested_department]
    if red_flag_depts:
        return Counter(red_flag_depts).most_common(1)[0][0]
    return Counter(departments).most_common(1)[0][0]


def build_reasoning(matched_symptoms, urgency):
    if not matched_symptoms:
        return (
            "No specific symptoms were recognized from the description provided. "
            "Please consult a general physician for an in-person evaluation, or provide more detail."
        )

    names = ", ".join(s.name for s in matched_symptoms)
    lines = [f"Detected symptoms: {names}."]

    red_flags = [s.name for s in matched_symptoms if s.red_flag]
    if red_flags:
        lines.append(
            f"{', '.join(red_flags)} {'is' if len(red_flags) == 1 else 'are'} considered red-flag symptom(s) "
            "requiring urgent clinical assessment."
        )

    urgency_notes = {
        TriageAssessment.Urgency.EMERGENCY: "This combination indicates a potential emergency — seek immediate emergency care.",
        TriageAssessment.Urgency.HIGH: "This combination suggests prompt/urgent medical evaluation is recommended.",
        TriageAssessment.Urgency.MODERATE: "A doctor consultation is recommended soon.",
        TriageAssessment.Urgency.LOW: "A routine appointment is recommended.",
    }
    lines.append(urgency_notes[urgency])
    return " ".join(lines)


def run_rule_based_triage(symptoms_text):
    """Returns (matched_symptoms, urgency, department, reasoning)."""
    matched = match_symptoms(symptoms_text)
    urgency = determine_urgency(matched)
    department = determine_department(matched)
    reasoning = build_reasoning(matched, urgency)
    return matched, urgency, department, reasoning
