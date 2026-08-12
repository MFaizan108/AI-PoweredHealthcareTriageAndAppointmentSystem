from unittest.mock import patch

from django.test import TestCase

from .evaluation import run_rule_engine_evaluation, summarize
from .llm_evaluation import evaluate_provider
from .models import AIProviderSettings


class RuleEngineEvaluationTests(TestCase):
    def test_canonical_matrix_passes_against_seeded_symptoms(self):
        results = run_rule_engine_evaluation()
        summary = summarize(results)
        failed = [r for r in results if not r["passed"]]
        self.assertEqual(failed, [], f"Evaluation cases failed: {failed}")
        self.assertEqual(summary["accuracy"], 1.0)
        self.assertEqual({r["id"] for r in results}, {
            "red_flag_to_emergency", "high_severity_to_high", "multiple_moderate_to_moderate",
            "low_severity_to_low", "unknown_to_safe_fallback",
        })

    def test_unknown_case_matches_no_symptoms(self):
        results = run_rule_engine_evaluation()
        unknown = next(r for r in results if r["id"] == "unknown_to_safe_fallback")
        self.assertEqual(unknown["matched_symptoms"], [])
        self.assertIsNone(unknown["department"])


class LLMEvaluationTests(TestCase):
    def test_success_call_is_classified_as_success(self):
        with patch("triage.llm.requests.post") as mock_post:
            mock_post.return_value.raise_for_status.return_value = None
            mock_post.return_value.json.return_value = {"response": "The patient reports mild symptoms."}
            metrics = evaluate_provider(AIProviderSettings.Provider.OLLAMA, samples=[
                {"symptoms_text": "fever", "detected_symptom_names": ["Fever"], "urgency": "low"},
            ])
        self.assertEqual(metrics["success_rate"], 1.0)
        self.assertEqual(metrics["calls"][0]["outcome"], "success")
        self.assertGreaterEqual(metrics["avg_latency_ms"], 0)

    def test_connection_failure_is_classified_as_failure(self):
        with patch("triage.llm.requests.post", side_effect=ConnectionError("Connection refused")):
            metrics = evaluate_provider(AIProviderSettings.Provider.OLLAMA, samples=[
                {"symptoms_text": "fever", "detected_symptom_names": ["Fever"], "urgency": "low"},
            ])
        self.assertEqual(metrics["failure_rate"], 1.0)
        self.assertEqual(metrics["calls"][0]["outcome"], "failure")

    def test_timeout_is_classified_as_timeout(self):
        import requests

        with patch("triage.llm.requests.post", side_effect=requests.exceptions.Timeout("Read timed out.")):
            metrics = evaluate_provider(AIProviderSettings.Provider.OLLAMA, samples=[
                {"symptoms_text": "fever", "detected_symptom_names": ["Fever"], "urgency": "low"},
            ])
        self.assertEqual(metrics["timeout_rate"], 1.0)
        self.assertEqual(metrics["calls"][0]["outcome"], "timeout")

    def test_empty_response_is_classified_as_invalid_response(self):
        with patch("triage.llm.requests.post") as mock_post:
            mock_post.return_value.raise_for_status.return_value = None
            mock_post.return_value.json.return_value = {"response": ""}
            metrics = evaluate_provider(AIProviderSettings.Provider.OLLAMA, samples=[
                {"symptoms_text": "fever", "detected_symptom_names": ["Fever"], "urgency": "low"},
            ])
        self.assertEqual(metrics["invalid_response_rate"], 1.0)
        self.assertEqual(metrics["calls"][0]["outcome"], "invalid_response")

    def test_unconfigured_groq_key_fails_without_touching_persisted_settings(self):
        """Probing 'groq' must not require (or mutate) the admin's persisted provider choice —
        it evaluates via an unsaved settings snapshot."""
        self.assertEqual(AIProviderSettings.get_solo().provider, AIProviderSettings.Provider.OLLAMA)
        metrics = evaluate_provider(AIProviderSettings.Provider.GROQ, samples=[
            {"symptoms_text": "fever", "detected_symptom_names": ["Fever"], "urgency": "low"},
        ])
        self.assertEqual(metrics["failure_rate"], 1.0)
        # The real singleton was never touched.
        self.assertEqual(AIProviderSettings.get_solo().provider, AIProviderSettings.Provider.OLLAMA)
