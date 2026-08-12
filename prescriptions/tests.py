from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from departments.models import Department
from doctors.models import Doctor
from patients.models import Patient

from .models import Prescription

TEST_OVERRIDES = dict(
    CELERY_TASK_ALWAYS_EAGER=True, MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
)


@override_settings(**TEST_OVERRIDES)
class PrescriptionTests(APITestCase):
    def setUp(self):
        dept = Department.objects.create(name="Endocrinology")
        self.doctor_user = User.objects.create_user(
            username="rx_doc", email="rx_doc@example.com", password="x", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.doctor.department = dept
        self.doctor.save()

        self.patient_user = User.objects.create_user(
            username="rx_pat", email="rx_pat@example.com", password="x", role=User.Role.PATIENT
        )
        self.patient = Patient.objects.get(user=self.patient_user)

        self.other_patient_user = User.objects.create_user(
            username="rx_pat2", email="rx_pat2@example.com", password="x", role=User.Role.PATIENT
        )
        self.lab_staff = User.objects.create_user(
            username="rx_lab", email="rx_lab@example.com", password="x", role=User.Role.LAB_STAFF
        )

        self.prescription = Prescription.objects.create(patient=self.patient, doctor=self.doctor, notes="Take with food.")

    def test_doctor_can_create_prescription_with_nested_items(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post(
            "/api/prescriptions/",
            {
                "patient": self.patient.id,
                "notes": "3-day course",
                "items": [{"medicine_name": "Amoxicillin", "dosage": "500mg", "frequency": "3x/day", "duration": "3 days"}],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(len(resp.data["items"]), 1)
        self.assertEqual(resp.data["items"][0]["medicine_name"], "Amoxicillin")

    def test_patient_cannot_create_prescription(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post("/api/prescriptions/", {"patient": self.patient.id})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_can_view_own_prescription(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get("/api/prescriptions/")
        self.assertEqual(resp.data["count"], 1)

    def test_patient_cannot_view_another_patients_prescription(self):
        self.client.force_authenticate(self.other_patient_user)
        resp = self.client.get(f"/api/prescriptions/{self.prescription.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_lab_staff_has_no_access_to_prescriptions(self):
        self.client.force_authenticate(self.lab_staff)
        resp = self.client.get("/api/prescriptions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_pdf_export_returns_valid_pdf(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get(f"/api/prescriptions/{self.prescription.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF"))

    def test_pdf_export_denied_for_another_patient(self):
        self.client.force_authenticate(self.other_patient_user)
        resp = self.client.get(f"/api/prescriptions/{self.prescription.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_creating_prescription_notifies_patient(self):
        from notifications.models import Notification

        self.client.force_authenticate(self.doctor_user)
        self.client.post("/api/prescriptions/", {"patient": self.patient.id, "notes": "New Rx"})
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.patient_user, notification_type=Notification.NotificationType.PRESCRIPTION_AVAILABLE
            ).exists()
        )
