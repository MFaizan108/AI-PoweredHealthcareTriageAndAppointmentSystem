"""Layer 1 evaluation — a fixed, named test-case matrix for the rule-based triage engine.

Distinct from triage/tests.py: those are regression unit tests (pass/fail on individual
behaviors). This module is the evaluation matrix the roadmap asks for — a reusable,
human-readable report of how the rule engine handles each of the required scenario
categories (red flag, high, moderate, low, unknown), runnable both from tests and from
the `evaluate_ai` management command.

Depends on the canonical symptom set from `seed_triage_data` (idempotent `update_or_create`,
safe to call repeatedly) so the matrix is meaningful against a fresh/empty database too.
"""

from django.core.management import call_command

from .models import TriageAssessment
from .rules_engine import run_rule_based_triage

U = TriageAssessment.Urgency

RULE_ENGINE_MATRIX = [
    {
        "id": "red_flag_to_emergency",
        "description": "Red Flag -> Emergency",
        "symptoms_text": "I have severe chest pain and chest tightness.",
        "expected_urgency": U.EMERGENCY,
    },
    {
        "id": "high_severity_to_high",
        "description": "High Severity (no red flag) -> High",
        # Severe Headache (4) + Fracture/Injury (5) = 9, both non-red-flag, clears HIGH_THRESHOLD=8.
        "symptoms_text": "I have a severe headache and a suspected fracture after a fall.",
        "expected_urgency": U.HIGH,
    },
    {
        "id": "multiple_moderate_to_moderate",
        "description": "Multiple Moderate -> Moderate",
        # Abdominal Pain (3) + Nausea/Vomiting (2) = 5, clears MODERATE_THRESHOLD=4 but not HIGH.
        "symptoms_text": "I have abdominal pain and some nausea.",
        "expected_urgency": U.MODERATE,
    },
    {
        "id": "low_severity_to_low",
        "description": "Low Severity -> Low",
        "symptoms_text": "I have a mild skin rash on my arm.",
        "expected_urgency": U.LOW,
    },
    {
        "id": "unknown_to_safe_fallback",
        "description": "Unknown / unrecognized input -> Safe fallback (Low, no department)",
        "symptoms_text": "asdkfj qwerty nothing matches this text",
        "expected_urgency": U.LOW,
        "expect_no_match": True,
    },
]


def run_rule_engine_evaluation():
    """Runs RULE_ENGINE_MATRIX against the live rule engine. Returns a list of per-case result
    dicts plus never mutates existing custom Symptom data (seed is an upsert-only fixture)."""
    call_command("seed_triage_data", verbosity=0)

    results = []
    for case in RULE_ENGINE_MATRIX:
        matched, urgency, department, reasoning = run_rule_based_triage(case["symptoms_text"])
        passed = urgency == case["expected_urgency"]
        if case.get("expect_no_match"):
            passed = passed and not matched
        results.append(
            {
                "id": case["id"],
                "description": case["description"],
                "symptoms_text": case["symptoms_text"],
                "expected_urgency": case["expected_urgency"],
                "actual_urgency": urgency,
                "matched_symptoms": [s.name for s in matched],
                "department": department.name if department else None,
                "passed": passed,
            }
        )
    return results


def summarize(results):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    return {"total": total, "passed": passed, "failed": total - passed, "accuracy": (passed / total) if total else 0.0}
