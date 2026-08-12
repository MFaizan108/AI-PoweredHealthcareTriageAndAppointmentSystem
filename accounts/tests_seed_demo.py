from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APITestCase

from .management.commands.seed_demo import DEMO_PASSWORD
from .models import User

DEMO_PATIENTS = ["patient_ali", "patient_mariam", "patient_zain"]
DEMO_DOCTORS = ["dr_ayesha", "dr_bilal", "dr_sara"]


class SeedDemoCommandTests(TestCase):
    def test_creates_one_account_per_role_with_a_usable_hashed_password(self):
        call_command("seed_demo", verbosity=0)

        admin = User.objects.get(username="demo_admin")
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_superuser)
        # A hashed password must never equal the plaintext, and must verify via check_password.
        self.assertNotEqual(admin.password, DEMO_PASSWORD)
        self.assertTrue(admin.check_password(DEMO_PASSWORD))

        self.assertEqual(User.objects.filter(username__in=DEMO_DOCTORS, role=User.Role.DOCTOR).count(), 3)
        self.assertEqual(User.objects.filter(username__in=DEMO_PATIENTS, role=User.Role.PATIENT).count(), 3)
        self.assertEqual(User.objects.filter(username="reception_uzma", role=User.Role.RECEPTIONIST).count(), 1)
        self.assertEqual(User.objects.filter(username="lab_hassan", role=User.Role.LAB_STAFF).count(), 1)

    def test_doctors_have_bookable_availability(self):
        """A doctor with zero DoctorAvailability rows is permanently unbookable (see docs/frontend.md)
        — the seed must leave every demo doctor with a real weekly schedule, not just a profile."""
        from doctors.models import Doctor

        call_command("seed_demo", verbosity=0)
        for username in DEMO_DOCTORS:
            doctor = Doctor.objects.get(user__username=username)
            self.assertTrue(doctor.availabilities.filter(is_active=True).exists(), f"{username} has no availability")

    def test_clinical_workflow_data_is_seeded_for_each_demo_patient(self):
        from ai_assistant.models import AssistantQueryLog
        from appointments.models import Appointment
        from billing.models import Invoice
        from laboratory.models import LabTest
        from medical_records.models import MedicalRecord
        from messaging.models import Message
        from notifications.models import Notification
        from prescriptions.models import Prescription
        from triage.models import TriageAssessment

        call_command("seed_demo", verbosity=0)

        def scoped(qs, field="patient__user__username"):
            return qs.filter(**{f"{field}__in": DEMO_PATIENTS}).count()

        self.assertEqual(scoped(Appointment.objects.all()), 4)
        self.assertEqual(scoped(MedicalRecord.objects.all()), 2)
        self.assertEqual(scoped(Prescription.objects.all()), 2)
        self.assertEqual(scoped(LabTest.objects.all()), 2)
        self.assertEqual(scoped(Invoice.objects.all()), 2)
        self.assertEqual(scoped(TriageAssessment.objects.all()), 2)
        self.assertEqual(Message.objects.filter(appointment__patient__user__username__in=DEMO_PATIENTS).count(), 2)
        self.assertEqual(Notification.objects.filter(recipient__username__in=DEMO_PATIENTS).count(), 3)
        self.assertEqual(AssistantQueryLog.objects.filter(user__username__in=DEMO_PATIENTS).count(), 1)

    def test_command_is_idempotent_when_run_twice_same_day(self):
        from appointments.models import Appointment

        call_command("seed_demo", verbosity=0)
        first_user_count = User.objects.filter(username__in=DEMO_PATIENTS + DEMO_DOCTORS).count()
        first_appointment_count = Appointment.objects.filter(patient__user__username__in=DEMO_PATIENTS).count()

        call_command("seed_demo", verbosity=0)
        second_user_count = User.objects.filter(username__in=DEMO_PATIENTS + DEMO_DOCTORS).count()
        second_appointment_count = Appointment.objects.filter(patient__user__username__in=DEMO_PATIENTS).count()

        self.assertEqual(first_user_count, second_user_count)
        self.assertEqual(first_appointment_count, second_appointment_count)


class SeedDemoLoginTests(APITestCase):
    def test_seeded_admin_can_actually_log_in(self):
        call_command("seed_demo", verbosity=0)
        resp = self.client.post("/api/accounts/login/", {"username": "demo_admin", "password": DEMO_PASSWORD})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIn("access", resp.data)
