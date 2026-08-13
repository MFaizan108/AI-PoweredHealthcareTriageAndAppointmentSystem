from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from departments.models import Department
from triage.models import Symptom, TriageAssessment
from triage.rules_engine import run_rule_based_triage


class RuleBasedTriageTests(TestCase):
    def setUp(self):
        self.emergency_dept = Department.objects.create(name="Emergency")
        self.general_dept = Department.objects.create(name="General Medicine")
        self.derma_dept = Department.objects.create(name="Dermatology")

        Symptom.objects.create(
            name="Fever",
            category=Symptom.Category.GENERAL,
            keywords="fever",
            severity_weight=2,
            red_flag=False,
            suggested_department=self.general_dept,
        )
        Symptom.objects.create(
            name="Severe Headache",
            category=Symptom.Category.NEUROLOGICAL,
            keywords="severe headache",
            severity_weight=4,
            red_flag=False,
            suggested_department=self.general_dept,
        )
        Symptom.objects.create(
            name="Difficulty Breathing",
            category=Symptom.Category.RESPIRATORY,
            keywords="difficulty breathing, shortness of breath",
            severity_weight=6,
            red_flag=True,
            suggested_department=self.emergency_dept,
        )
        Symptom.objects.create(
            name="Skin Rash",
            category=Symptom.Category.DERMATOLOGICAL,
            keywords="skin rash, rash",
            severity_weight=1,
            red_flag=False,
            suggested_department=self.derma_dept,
        )

    def test_blueprint_example_is_emergency(self):
        matched, urgency, department, reasoning = run_rule_based_triage("I have fever, severe headache and difficulty breathing.")
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

    def test_moderate_urgency_at_threshold_score(self):
        # Severe Headache (weight 4) alone hits the MODERATE_THRESHOLD exactly.
        matched, urgency, department, reasoning = run_rule_based_triage("I have a severe headache.")
        self.assertEqual(urgency, TriageAssessment.Urgency.MODERATE)

    def test_high_urgency_without_any_red_flag(self):
        # Severe Headache (4) + Persistent Vomiting (4) = 8, hits HIGH_THRESHOLD with no red-flag symptom involved.
        Symptom.objects.create(
            name="Persistent Vomiting",
            category=Symptom.Category.GASTROINTESTINAL,
            keywords="persistent vomiting",
            severity_weight=4,
            red_flag=False,
            suggested_department=self.general_dept,
        )
        matched, urgency, department, reasoning = run_rule_based_triage("I have a severe headache and persistent vomiting.")
        self.assertEqual(urgency, TriageAssessment.Urgency.HIGH)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TriageAssessAPITests(APITestCase):
    def setUp(self):
        from accounts.models import User
        from patients.models import Patient

        self.emergency_dept = Department.objects.create(name="Emergency Room")
        self.general_dept = Department.objects.create(name="General Medicine API")
        Symptom.objects.create(
            name="Fever API",
            category=Symptom.Category.GENERAL,
            keywords="fever",
            severity_weight=2,
            red_flag=False,
            suggested_department=self.general_dept,
        )
        Symptom.objects.create(
            name="Chest Pain API",
            category=Symptom.Category.CARDIAC,
            keywords="chest pain",
            severity_weight=7,
            red_flag=True,
            suggested_department=self.emergency_dept,
        )

        self.patient_user = User.objects.create_user(
            username="triage_pat", email="triage_pat@example.com", password="x", role=User.Role.PATIENT
        )
        self.patient = Patient.objects.get(user=self.patient_user)
        self.other_patient_user = User.objects.create_user(
            username="triage_pat2", email="triage_pat2@example.com", password="x", role=User.Role.PATIENT
        )
        self.doctor_user = User.objects.create_user(
            username="triage_doc", email="triage_doc@example.com", password="x", role=User.Role.DOCTOR
        )
        self.receptionist = User.objects.create_user(
            username="triage_recep", email="triage_recep@example.com", password="x", role=User.Role.RECEPTIONIST
        )
        self.admin = User.objects.create_user(
            username="triage_admin", email="triage_admin@example.com", password="x", role=User.Role.ADMIN
        )

    def test_patient_assess_persists_rule_based_result_even_without_ai(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post(
            "/api/triage/assess/", {"symptoms_text": "severe chest pain", "use_ai_summary": False}, format="json"
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["urgency"], "emergency")
        self.assertEqual(resp.data["disclaimer"], TriageAssessment.DISCLAIMER)
        self.assertEqual(resp.data["ai_summary"], "")
        self.assertEqual(resp.data["ai_summary_status"], "not_requested")

    def test_assess_degrades_gracefully_when_llm_call_fails(self):
        from unittest.mock import patch

        self.client.force_authenticate(self.patient_user)
        with patch("triage.llm.requests.post", side_effect=ConnectionError("Ollama unreachable")):
            resp = self.client.post("/api/triage/assess/", {"symptoms_text": "fever", "use_ai_summary": True}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        # Rule-based urgency ("fever" alone, weight 2, below MODERATE_THRESHOLD) is always returned even though the LLM failed.
        self.assertEqual(resp.data["urgency"], "low")
        self.assertEqual(resp.data["ai_summary"], "")
        self.assertNotEqual(resp.data["ai_summary_error"], "")
        self.assertEqual(resp.data["ai_summary_status"], "failed")

    def test_ai_summary_generation_runs_as_a_background_task_not_inline(self):
        """The view must hand off to Celery rather than calling the LLM inline — this is the whole point
        of Phase 7's async triage change (a slow/unreachable LLM must never block the HTTP response)."""
        from unittest.mock import patch

        self.client.force_authenticate(self.patient_user)
        with patch("triage.views.generate_ai_summary_task.delay") as mock_delay:
            resp = self.client.post("/api/triage/assess/", {"symptoms_text": "fever", "use_ai_summary": True}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        mock_delay.assert_called_once_with(resp.data["id"])
        # Without the (mocked-away) task ever running, the summary must still be unset/pending — proving
        # the rule-based response does not wait on it.
        self.assertEqual(resp.data["ai_summary_status"], "pending")

    def test_successful_ai_summary_marks_status_ready(self):
        from unittest.mock import patch

        self.client.force_authenticate(self.patient_user)
        with patch("triage.llm.requests.post") as mock_post:
            mock_post.return_value.raise_for_status.return_value = None
            mock_post.return_value.json.return_value = {"response": "Patient reports mild fever."}
            resp = self.client.post("/api/triage/assess/", {"symptoms_text": "fever", "use_ai_summary": True}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["ai_summary_status"], "ready")
        self.assertEqual(resp.data["ai_summary"], "Patient reports mild fever.")

    def test_patient_cannot_create_assessment_for_another_patient(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post(
            "/api/triage/assess/",
            {"symptoms_text": "fever", "patient": self.other_patient_user.patient_profile.id, "use_ai_summary": False},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        # A patient's own `patient` link is always forced server-side, ignoring any submitted patient id.
        self.assertEqual(resp.data["patient"], self.patient.id)

    def test_receptionist_can_create_but_not_list_assessments(self):
        self.client.force_authenticate(self.receptionist)
        create_resp = self.client.post(
            "/api/triage/assess/",
            {"symptoms_text": "fever", "patient": self.patient.id, "use_ai_summary": False},
            format="json",
        )
        self.assertEqual(create_resp.status_code, 201, create_resp.data)

        list_resp = self.client.get("/api/triage/assessments/")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data["count"], 0)

    def _create_assessment_linked_to_doctor(self):
        """A doctor can only review an assessment tied to one of their own appointments — build that link."""
        import datetime

        from appointments.models import Appointment
        from doctors.models import Doctor

        doctor = Doctor.objects.filter(user=self.doctor_user).first()
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=doctor,
            appointment_date=datetime.date.today(),
            slot_start_time=datetime.time(9, 0),
            slot_end_time=datetime.time(9, 20),
        )
        self.client.force_authenticate(self.patient_user)
        create_resp = self.client.post(
            "/api/triage/assess/",
            {"symptoms_text": "fever", "appointment": appointment.id, "use_ai_summary": False},
            format="json",
        )
        self.assertEqual(create_resp.status_code, 201, create_resp.data)
        return create_resp.data["id"]

    def test_doctor_can_review_assessment(self):
        assessment_id = self._create_assessment_linked_to_doctor()

        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post(
            f"/api/triage/assessments/{assessment_id}/review/", {"clinician_agrees": True, "clinician_notes": "Agreed."}
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data["clinician_agrees"])

    def test_patient_cannot_review_assessment(self):
        assessment_id = self._create_assessment_linked_to_doctor()

        self.client.force_authenticate(self.patient_user)
        resp = self.client.post(f"/api/triage/assessments/{assessment_id}/review/", {"clinician_agrees": True})
        self.assertEqual(resp.status_code, 403)

    def test_ai_provider_settings_is_admin_only(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get("/api/triage/ai-settings/")
        self.assertEqual(resp.status_code, 403)

        self.client.force_authenticate(self.admin)
        resp = self.client.get("/api/triage/ai-settings/")
        self.assertEqual(resp.status_code, 200)

    def test_admin_can_switch_ai_provider_to_groq(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.patch("/api/triage/ai-settings/", {"provider": "groq", "groq_api_key": "gsk_test_key"})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["provider"], "groq")
        self.assertTrue(resp.data["groq_api_key_set"])


class EmergencyGuidanceTests(APITestCase):
    def setUp(self):
        from accounts.models import User

        self.admin = User.objects.create_user(
            username="eg_admin", email="eg_admin@example.com", password="x", role=User.Role.ADMIN
        )
        self.patient = User.objects.create_user(
            username="eg_pat", email="eg_pat@example.com", password="x", role=User.Role.PATIENT
        )

    def test_admin_can_create_emergency_guidance(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            "/api/triage/emergency-guidance/",
            {"urgency": "emergency", "title": "Call for help", "content": "Seek immediate care.", "emergency_numbers": "1122"},
        )
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_patient_can_read_but_not_write_emergency_guidance(self):
        self.client.force_authenticate(self.admin)
        self.client.post(
            "/api/triage/emergency-guidance/",
            {"urgency": "high", "title": "Seek care soon", "content": "Visit a clinic today."},
        )
        self.client.force_authenticate(self.patient)
        read_resp = self.client.get("/api/triage/emergency-guidance/")
        self.assertEqual(read_resp.data["count"], 1)

        write_resp = self.client.post(
            "/api/triage/emergency-guidance/",
            {"urgency": "low", "title": "x", "content": "y"},
        )
        self.assertEqual(write_resp.status_code, 403)


class TriageAssessThrottleTests(APITestCase):
    """Every call to /api/triage/assess/ can trigger a real LLM request — it must be throttled
    more strictly than ordinary CRUD, or a single account could burn LLM cost/compute unbounded."""

    def setUp(self):
        from django.core.cache import cache

        from accounts.models import User

        cache.clear()
        self.patient_user = User.objects.create_user(
            username="throttle_pat", email="throttle_pat@example.com", password="x", role=User.Role.PATIENT
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_exceeding_the_ai_rate_limit_returns_429(self):
        from unittest.mock import patch

        from .throttles import AIRateThrottle

        # SimpleRateThrottle.THROTTLE_RATES is a class attribute snapshotted from
        # api_settings.DEFAULT_THROTTLE_RATES at import time, not re-read per request — so
        # override_settings(REST_FRAMEWORK=...) alone can't lower it for a fast test. Patch
        # get_rate() directly instead (it *is* called fresh on every request).
        with patch.object(AIRateThrottle, "get_rate", return_value="2/min"):
            self.client.force_authenticate(self.patient_user)
            for _ in range(2):
                resp = self.client.post("/api/triage/assess/", {"symptoms_text": "fever", "use_ai_summary": False}, format="json")
                self.assertEqual(resp.status_code, 201, resp.data)

            resp = self.client.post("/api/triage/assess/", {"symptoms_text": "fever", "use_ai_summary": False}, format="json")
            self.assertEqual(resp.status_code, 429, resp.data)
