import datetime

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from departments.models import Department

from .models import Doctor, DoctorAvailability, DoctorLeave


class DoctorViewSetTests(APITestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="ENT")
        self.other_dept = Department.objects.create(name="Orthopedics")

        self.doctor_user = User.objects.create_user(
            username="doc_x", email="doc_x@example.com", password="x", role=User.Role.DOCTOR,
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.doctor.department = self.dept
        self.doctor.save()

        self.other_doctor_user = User.objects.create_user(
            username="doc_y", email="doc_y@example.com", password="x", role=User.Role.DOCTOR,
        )
        self.other_doctor = Doctor.objects.filter(user=self.other_doctor_user).first()
        self.other_doctor.department = self.other_dept
        self.other_doctor.save()

        self.admin = User.objects.create_user(username="doc_admin", email="doc_admin@example.com", password="x", role=User.Role.ADMIN)
        self.patient = User.objects.create_user(username="doc_patient", email="doc_patient@example.com", password="x", role=User.Role.PATIENT)

    def test_doctor_profile_auto_created_on_user_creation(self):
        self.assertIsNotNone(self.doctor)

    def test_anyone_authenticated_can_list_doctors(self):
        self.client.force_authenticate(self.patient)
        resp = self.client.get("/api/doctors/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_filter_doctors_by_department(self):
        self.client.force_authenticate(self.patient)
        resp = self.client.get(f"/api/doctors/?department={self.dept.id}")
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["id"], self.doctor.id)

    def test_doctor_can_update_own_profile(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.patch(f"/api/doctors/{self.doctor.id}/", {"bio": "Updated bio"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

    def test_doctor_cannot_update_another_doctors_profile(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.patch(f"/api/doctors/{self.other_doctor.id}/", {"bio": "Hijacked"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_cannot_deactivate_a_doctor(self):
        self.client.force_authenticate(self.patient)
        resp = self.client.patch(f"/api/doctors/{self.doctor.id}/", {"is_active": False})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class DoctorAvailabilityTests(APITestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username="avail_doc", email="avail_doc@example.com", password="x", role=User.Role.DOCTOR,
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.admin = User.objects.create_user(username="avail_admin", email="avail_admin@example.com", password="x", role=User.Role.ADMIN)

    def test_doctor_can_create_own_availability(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post(
            "/api/doctors/availability/",
            {"doctor": self.doctor.id, "weekday": 0, "start_time": "09:00:00", "end_time": "12:00:00", "slot_duration_minutes": 15},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

    def test_availability_end_before_start_is_rejected(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            "/api/doctors/availability/",
            {"doctor": self.doctor.id, "weekday": 0, "start_time": "12:00:00", "end_time": "09:00:00"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_availability_by_doctor(self):
        DoctorAvailability.objects.create(doctor=self.doctor, weekday=1, start_time=datetime.time(9, 0), end_time=datetime.time(11, 0))
        self.client.force_authenticate(self.admin)
        resp = self.client.get(f"/api/doctors/availability/?doctor={self.doctor.id}")
        self.assertEqual(resp.data["count"], 1)


class DoctorLeaveTests(APITestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username="leave_doc", email="leave_doc@example.com", password="x", role=User.Role.DOCTOR,
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.other_doctor_user = User.objects.create_user(
            username="leave_doc2", email="leave_doc2@example.com", password="x", role=User.Role.DOCTOR,
        )

    def test_doctor_can_request_own_leave(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post(
            "/api/doctors/leaves/",
            {"doctor": self.doctor.id, "start_date": "2026-09-01", "end_date": "2026-09-05", "reason": "Conference"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

    def test_doctor_cannot_create_leave_for_another_doctor(self):
        other_doctor = Doctor.objects.filter(user=self.other_doctor_user).first()
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post(
            "/api/doctors/leaves/",
            {"doctor": other_doctor.id, "start_date": "2026-09-01", "end_date": "2026-09-05"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
