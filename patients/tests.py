from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import Patient


class PatientAccessTests(APITestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            username="pat_a",
            email="pat_a@example.com",
            password="x",
            role=User.Role.PATIENT,
            first_name="Ali",
        )
        self.other_patient_user = User.objects.create_user(
            username="pat_b",
            email="pat_b@example.com",
            password="x",
            role=User.Role.PATIENT,
        )
        self.doctor_user = User.objects.create_user(
            username="pat_doc",
            email="pat_doc@example.com",
            password="x",
            role=User.Role.DOCTOR,
        )
        self.receptionist = User.objects.create_user(
            username="pat_recep",
            email="pat_recep@example.com",
            password="x",
            role=User.Role.RECEPTIONIST,
        )

    def test_patient_profile_auto_created_on_user_creation(self):
        self.assertTrue(Patient.objects.filter(user=self.patient_user).exists())

    def test_patient_can_only_see_own_profile_in_list(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get("/api/patients/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["user"]["id"], self.patient_user.id)

    def test_patient_cannot_retrieve_another_patients_profile(self):
        other = Patient.objects.get(user=self.other_patient_user)
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get(f"/api/patients/{other.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_doctor_can_see_all_patients(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.get("/api/patients/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_receptionist_can_search_patients_by_name(self):
        self.client.force_authenticate(self.receptionist)
        resp = self.client.get("/api/patients/?search=Ali")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["user"]["id"], self.patient_user.id)

    def test_me_endpoint_returns_own_profile(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get("/api/patients/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["user"]["id"], self.patient_user.id)
