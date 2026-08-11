import datetime

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from departments.models import Department
from doctors.models import Doctor
from patients.models import Patient

from .models import Diagnosis, MedicalRecord


class MedicalRecordTests(APITestCase):
    def setUp(self):
        dept = Department.objects.create(name="Internal Medicine")
        self.doctor_user = User.objects.create_user(username="mr_doc", email="mr_doc@example.com", password="x", role=User.Role.DOCTOR)
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.doctor.department = dept
        self.doctor.save()

        self.other_doctor_user = User.objects.create_user(username="mr_doc2", email="mr_doc2@example.com", password="x", role=User.Role.DOCTOR)

        self.patient_user = User.objects.create_user(username="mr_pat", email="mr_pat@example.com", password="x", role=User.Role.PATIENT)
        self.patient = Patient.objects.get(user=self.patient_user)

        self.other_patient_user = User.objects.create_user(username="mr_pat2", email="mr_pat2@example.com", password="x", role=User.Role.PATIENT)

        self.receptionist = User.objects.create_user(username="mr_recep", email="mr_recep@example.com", password="x", role=User.Role.RECEPTIONIST)

        self.record = MedicalRecord.objects.create(
            patient=self.patient, doctor=self.doctor, visit_date=datetime.date.today(), consultation_notes="Routine checkup.",
        )

    def test_doctor_can_create_medical_record(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post(
            "/api/medical-records/",
            {"patient": self.patient.id, "visit_date": datetime.date.today().isoformat(), "consultation_notes": "Follow-up visit."},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["doctor"], self.doctor.id)

    def test_patient_cannot_create_medical_record(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post(
            "/api/medical-records/",
            {"patient": self.patient.id, "visit_date": datetime.date.today().isoformat()},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_receptionist_cannot_view_medical_records(self):
        self.client.force_authenticate(self.receptionist)
        resp = self.client.get("/api/medical-records/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_patient_can_view_own_record(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get("/api/medical-records/")
        self.assertEqual(resp.data["count"], 1)

    def test_patient_cannot_view_another_patients_record(self):
        self.client.force_authenticate(self.other_patient_user)
        resp = self.client.get(f"/api/medical-records/{self.record.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_treating_doctor_cannot_edit_record(self):
        self.client.force_authenticate(self.other_doctor_user)
        resp = self.client.patch(f"/api/medical-records/{self.record.id}/", {"consultation_notes": "Hijacked"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_treating_doctor_can_add_diagnosis(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post(
            "/api/medical-records/diagnoses/",
            {"medical_record": self.record.id, "description": "Mild hypertension."},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

    def test_patient_can_read_diagnosis_on_own_record(self):
        Diagnosis.objects.create(medical_record=self.record, description="Seasonal allergy.")
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get("/api/medical-records/diagnoses/")
        self.assertEqual(resp.data["count"], 1)

    def test_follow_up_fields_are_saved(self):
        self.client.force_authenticate(self.doctor_user)
        follow_up = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
        resp = self.client.patch(
            f"/api/medical-records/{self.record.id}/",
            {"follow_up_date": follow_up, "follow_up_notes": "Recheck blood pressure."},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.record.refresh_from_db()
        self.assertEqual(self.record.follow_up_date.isoformat(), follow_up)
