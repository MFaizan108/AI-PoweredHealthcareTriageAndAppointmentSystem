import datetime
from unittest.mock import patch

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from departments.models import Department
from doctors.models import Doctor
from patients.models import Patient

from .models import AssistantQueryLog, HospitalFAQ

TEST_OVERRIDES = dict(
    CELERY_TASK_ALWAYS_EAGER=True, MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
)


@override_settings(**TEST_OVERRIDES)
class AssistantAskPermissionTests(APITestCase):
    def setUp(self):
        dept = Department.objects.create(name="Assistant Dept")
        self.doctor_user = User.objects.create_user(
            username="asst_doc", email="asst_doc@example.com", password="x", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.doctor.department = dept
        self.doctor.save()

        self.patient_user = User.objects.create_user(
            username="asst_pat_a", email="asst_pat_a@example.com", password="x", role=User.Role.PATIENT
        )
        self.patient = Patient.objects.get(user=self.patient_user)

        self.other_patient_user = User.objects.create_user(
            username="asst_pat_b", email="asst_pat_b@example.com", password="x", role=User.Role.PATIENT
        )
        self.other_patient = Patient.objects.get(user=self.other_patient_user)

        from appointments.models import Appointment

        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=datetime.date.today() + datetime.timedelta(days=3),
            slot_start_time=datetime.time(9, 0),
            slot_end_time=datetime.time(9, 20),
            token_number="A-101",
        )
        self.other_appointment = Appointment.objects.create(
            patient=self.other_patient,
            doctor=self.doctor,
            appointment_date=datetime.date.today() + datetime.timedelta(days=3),
            slot_start_time=datetime.time(9, 20),
            slot_end_time=datetime.time(9, 40),
            token_number="A-102",
        )

    def test_doctor_role_cannot_use_patient_assistant(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post("/api/ai-assistant/ask/", {"message": "When is my next appointment?"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @patch("ai_assistant.views.ask_llm")
    def test_patient_a_asking_about_patient_b_only_ever_retrieves_patient_as_own_data(self, mock_ask_llm):
        """Patient A cannot pull Patient B's data through the assistant — the retriever is scoped to the
        authenticated user's own Patient record regardless of what the free-text question references."""
        mock_ask_llm.return_value = ("Mock response.", "ollama", None)

        self.client.force_authenticate(self.patient_user)
        self.client.post("/api/ai-assistant/ask/", {"message": "What is my next appointment?"})

        sent_prompt = mock_ask_llm.call_args[0][1]  # ask_llm(system_prompt, prompt)
        retrieved_patient_data = sent_prompt.split("HOSPITAL FAQs:")[0]  # everything the retriever pulled from the DB
        self.assertIn(self.appointment.token_number, retrieved_patient_data)
        self.assertNotIn(self.other_appointment.token_number, retrieved_patient_data)

    @patch("ai_assistant.views.ask_llm")
    def test_successful_query_is_logged_for_the_asking_user(self, mock_ask_llm):
        mock_ask_llm.return_value = ("You have an appointment soon.", "groq", None)
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post("/api/ai-assistant/ask/", {"message": "When is my appointment?"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["provider_used"], "groq")

        log = AssistantQueryLog.objects.filter(user=self.patient_user).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.response, "You have an appointment soon.")

    @patch("ai_assistant.views.ask_llm")
    def test_llm_failure_returns_friendly_fallback_not_500(self, mock_ask_llm):
        mock_ask_llm.return_value = (None, "ollama", "Connection refused")
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post("/api/ai-assistant/ask/", {"message": "Hello"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("unavailable", resp.data["response"].lower())
        self.assertEqual(resp.data["error"], "Connection refused")

    def test_user_can_only_see_own_assistant_history(self):
        AssistantQueryLog.objects.create(user=self.patient_user, message="hi", response="hello")
        AssistantQueryLog.objects.create(user=self.other_patient_user, message="hi", response="hello")

        self.client.force_authenticate(self.patient_user)
        resp = self.client.get("/api/ai-assistant/history/")
        self.assertEqual(resp.data["count"], 1)


@override_settings(**TEST_OVERRIDES)
class HospitalFAQTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="faq_admin", email="faq_admin@example.com", password="x", role=User.Role.ADMIN
        )
        self.patient = User.objects.create_user(
            username="faq_pat", email="faq_pat@example.com", password="x", role=User.Role.PATIENT
        )

    def test_authenticated_user_can_read_faqs(self):
        HospitalFAQ.objects.create(question="What are visiting hours?", answer="9am-5pm daily.")
        self.client.force_authenticate(self.patient)
        resp = self.client.get("/api/ai-assistant/faqs/")
        self.assertEqual(resp.data["count"], 1)

    def test_patient_cannot_create_faq(self):
        self.client.force_authenticate(self.patient)
        resp = self.client.post("/api/ai-assistant/faqs/", {"question": "Q?", "answer": "A."})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_faq(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post("/api/ai-assistant/faqs/", {"question": "Q?", "answer": "A."})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
