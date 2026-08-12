from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class AnalyticsAccessTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="an_admin", email="an_admin@example.com", password="x", role=User.Role.ADMIN
        )
        self.doctor = User.objects.create_user(username="an_doc", email="an_doc@example.com", password="x", role=User.Role.DOCTOR)
        self.patient = User.objects.create_user(
            username="an_pat", email="an_pat@example.com", password="x", role=User.Role.PATIENT
        )
        self.receptionist = User.objects.create_user(
            username="an_recep", email="an_recep@example.com", password="x", role=User.Role.RECEPTIONIST
        )

    def test_admin_can_access_all_three_analytics_endpoints(self):
        self.client.force_authenticate(self.admin)
        for path in ("/api/analytics/patients/", "/api/analytics/appointments/", "/api/analytics/ai/"):
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, status.HTTP_200_OK, path)

    def test_doctor_cannot_access_patient_analytics(self):
        self.client.force_authenticate(self.doctor)
        resp = self.client.get("/api/analytics/patients/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_receptionist_cannot_access_appointment_analytics(self):
        self.client.force_authenticate(self.receptionist)
        resp = self.client.get("/api/analytics/appointments/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_cannot_access_ai_analytics(self):
        self.client.force_authenticate(self.patient)
        resp = self.client.get("/api/analytics/ai/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_analytics_response_shape(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get("/api/analytics/patients/")
        for key in (
            "total_patients",
            "new_patients_this_month",
            "gender_distribution",
            "age_distribution",
            "department_utilization",
        ):
            self.assertIn(key, resp.data)

    def test_ai_analytics_includes_monitoring_disclaimer_note(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get("/api/analytics/ai/")
        self.assertIn("note", resp.data)
        self.assertIn("Monitoring metric only", resp.data["note"])
