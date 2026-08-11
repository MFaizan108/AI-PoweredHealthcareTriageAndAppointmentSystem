from django.test import TestCase

from departments.models import Department
from triage.models import Symptom, TriageAssessment
from triage.rules_engine import run_rule_based_triage


class RuleBasedTriageTests(TestCase):
    def setUp(self):
        self.emergency_dept = Department.objects.create(name="Emergency")
        self.general_dept = Department.objects.create(name="General Medicine")
        self.derma_dept = Department.objects.create(name="Dermatology")

        Symptom.objects.create(
            name="Fever", category=Symptom.Category.GENERAL, keywords="fever",
            severity_weight=2, red_flag=False, suggested_department=self.general_dept,
        )
        Symptom.objects.create(
            name="Severe Headache", category=Symptom.Category.NEUROLOGICAL, keywords="severe headache",
            severity_weight=4, red_flag=False, suggested_department=self.general_dept,
        )
        Symptom.objects.create(
            name="Difficulty Breathing", category=Symptom.Category.RESPIRATORY,
            keywords="difficulty breathing, shortness of breath",
            severity_weight=6, red_flag=True, suggested_department=self.emergency_dept,
        )
        Symptom.objects.create(
            name="Skin Rash", category=Symptom.Category.DERMATOLOGICAL, keywords="skin rash, rash",
            severity_weight=1, red_flag=False, suggested_department=self.derma_dept,
        )

    def test_blueprint_example_is_emergency(self):
        matched, urgency, department, reasoning = run_rule_based_triage(
            "I have fever, severe headache and difficulty breathing."
        )
        self.assertEqual(urgency, TriageAssessment.Urgency.EMERGENCY)
        self.assertEqual(department, self.emergency_dept)
        self.assertIn("Difficulty Breathing", [s.name for s in matched])
        self.assertIn("red-flag", reasoning.lower())

    def test_low_urgency_single_mild_symptom(self):
        matched, urgency, department, reasoning = run_rule_based_triage("I have a mild skin rash on my arm.")
        self.assertEqual(urgency, TriageAssessment.Urgency.LOW)
        self.assertEqual(department, self.derma_dept)

    def test_no_symptoms_matched_defaults_low(self):
        matched, urgency, department, reasoning = run_rule_based_triage("I feel a bit strange today.")
        self.assertEqual(matched, [])
        self.assertEqual(urgency, TriageAssessment.Urgency.LOW)
        self.assertIsNone(department)

    def test_red_flag_always_wins_even_with_low_total_score(self):
        # A single red-flag symptom (weight 6) must escalate to EMERGENCY regardless of thresholds.
        matched, urgency, department, reasoning = run_rule_based_triage("shortness of breath only")
        self.assertEqual(urgency, TriageAssessment.Urgency.EMERGENCY)
