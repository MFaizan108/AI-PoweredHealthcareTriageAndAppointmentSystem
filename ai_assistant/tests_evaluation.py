from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from .rag_evaluation import run_rag_evaluation


class RagEvaluationTests(TestCase):
    def test_deny_and_allow_cases_both_pass(self):
        results = run_rag_evaluation()
        by_id = {r["id"]: r for r in results}

        deny = by_id["patient_a_asks_about_patient_b"]
        self.assertTrue(deny["passed"], deny)
        self.assertEqual(deny["actual"], "DENY")

        allow = by_id["patient_a_asks_about_own_data"]
        self.assertTrue(allow["passed"], allow)
        self.assertEqual(allow["actual"], "ALLOW")

    def test_sandbox_leaves_no_data_behind(self):
        from accounts.models import User

        run_rag_evaluation()
        self.assertFalse(User.objects.filter(username__startswith="rageval_").exists())


class EvaluateAiCommandTests(TestCase):
    def test_command_runs_end_to_end_and_reports_failures_gracefully(self):
        """The LLM section hits a real network call by default — force it to fail fast and
        deterministically here so the test doesn't depend on network access, while confirming
        the command still completes and produces a full report rather than crashing."""
        out = StringIO()
        with patch("triage.llm.requests.post", side_effect=ConnectionError("no network in test env")):
            call_command("evaluate_ai", stdout=out)
        output = out.getvalue()
        self.assertIn("Rule Engine Evaluation", output)
        self.assertIn("LLM Evaluation", output)
        self.assertIn("RAG Authorization Evaluation", output)
        self.assertIn("RAG must never bypass authorization: HOLDS", output)
