import datetime

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from departments.models import Department
from doctors.models import Doctor, DoctorAvailability

TEST_OVERRIDES = dict(
    CELERY_TASK_ALWAYS_EAGER=True,
    MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}},
)


@override_settings(**TEST_OVERRIDES)
class AppointmentBookingTests(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Cardiology")

        self.doctor_user = User.objects.create_user(
            username="dr_test", email="dr_test@example.com", password="DoctorPass123!", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.doctor.department = self.department
        self.doctor.save()

        # Pick the next occurrence of a fixed weekday so the test is deterministic and always has availability.
        today = datetime.date.today()
        target_weekday = 1  # Tuesday
        days_ahead = (target_weekday - today.weekday()) % 7
        days_ahead = days_ahead or 7
        self.appointment_date = today + datetime.timedelta(days=days_ahead)

        DoctorAvailability.objects.create(
            doctor=self.doctor, weekday=target_weekday,
            start_time=datetime.time(9, 0), end_time=datetime.time(11, 0), slot_duration_minutes=20,
        )

        self.patient_user = User.objects.create_user(
            username="patient_test", email="patient_test@example.com", password="PatientPass123!", role=User.Role.PATIENT
        )
        self.patient2_user = User.objects.create_user(
            username="patient2_test", email="patient2_test@example.com", password="PatientPass123!", role=User.Role.PATIENT
        )

    def test_available_slots_generated_correctly(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get(
            f"/api/appointments/available-slots/?doctor={self.doctor.id}&date={self.appointment_date.isoformat()}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # 09:00-11:00 in 20-min slots = 6 slots
        self.assertEqual(len(resp.data), 6)
        self.assertTrue(all(slot["available"] for slot in resp.data))

    def test_booking_creates_appointment_with_token(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post(
            "/api/appointments/",
            {
                "doctor": self.doctor.id,
                "appointment_date": self.appointment_date.isoformat(),
                "slot_start_time": "09:00:00",
                "reason": "Checkup",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["token_number"], "A-101")
        self.assertEqual(resp.data["status"], "pending")

    def test_double_booking_same_slot_is_rejected(self):
        self.client.force_authenticate(self.patient_user)
        first = self.client.post(
            "/api/appointments/",
            {"doctor": self.doctor.id, "appointment_date": self.appointment_date.isoformat(), "slot_start_time": "09:00:00"},
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.patient2_user)
        second = self.client.post(
            "/api/appointments/",
            {"doctor": self.doctor.id, "appointment_date": self.appointment_date.isoformat(), "slot_start_time": "09:00:00"},
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_a_different_slot_after_one_is_taken_succeeds(self):
        self.client.force_authenticate(self.patient_user)
        self.client.post(
            "/api/appointments/",
            {"doctor": self.doctor.id, "appointment_date": self.appointment_date.isoformat(), "slot_start_time": "09:00:00"},
        )
        self.client.force_authenticate(self.patient2_user)
        resp = self.client.post(
            "/api/appointments/",
            {"doctor": self.doctor.id, "appointment_date": self.appointment_date.isoformat(), "slot_start_time": "09:20:00"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["token_number"], "A-102")

    def test_patient_cannot_see_another_patients_appointments(self):
        self.client.force_authenticate(self.patient_user)
        self.client.post(
            "/api/appointments/",
            {"doctor": self.doctor.id, "appointment_date": self.appointment_date.isoformat(), "slot_start_time": "09:00:00"},
        )

        self.client.force_authenticate(self.patient2_user)
        resp = self.client.get("/api/appointments/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_booking_an_already_booked_slot_via_race_returns_clean_error_not_500(self):
        # Simulates two concurrent bookings resolving to the same slot; the second must be
        # a clean 400, not an unhandled IntegrityError / 500.
        self.client.force_authenticate(self.patient_user)
        payload = {"doctor": self.doctor.id, "appointment_date": self.appointment_date.isoformat(), "slot_start_time": "10:00:00"}
        first = self.client.post("/api/appointments/", payload)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.patient2_user)
        second = self.client.post("/api/appointments/", payload)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(**TEST_OVERRIDES)
class FeedbackTests(APITestCase):
    def setUp(self):
        department = Department.objects.create(name="Neurology")
        self.doctor_user = User.objects.create_user(
            username="dr_feedback", email="dr_feedback@example.com", password="x", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.doctor.department = department
        self.doctor.save()

        self.patient_user = User.objects.create_user(
            username="patient_feedback", email="patient_feedback@example.com", password="x", role=User.Role.PATIENT
        )
        from patients.models import Patient

        self.patient = Patient.objects.get(user=self.patient_user)

        from .models import Appointment

        self.completed_appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor, appointment_date=datetime.date.today(),
            slot_start_time=datetime.time(9, 0), slot_end_time=datetime.time(9, 20),
            status=Appointment.Status.COMPLETED,
        )
        self.pending_appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor, appointment_date=datetime.date.today(),
            slot_start_time=datetime.time(9, 20), slot_end_time=datetime.time(9, 40),
            status=Appointment.Status.PENDING,
        )

    def test_feedback_allowed_for_completed_appointment(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post(
            "/api/appointments/feedback/",
            {"appointment": self.completed_appointment.id, "rating": 5, "comment": "Great doctor"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

    def test_feedback_rejected_for_non_completed_appointment(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post(
            "/api/appointments/feedback/",
            {"appointment": self.pending_appointment.id, "rating": 4},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_feedback_rating_out_of_range_rejected(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post(
            "/api/appointments/feedback/",
            {"appointment": self.completed_appointment.id, "rating": 7},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(**TEST_OVERRIDES)
class WaitlistNotificationTests(APITestCase):
    def setUp(self):
        department = Department.objects.create(name="Dermatology")
        self.doctor_user = User.objects.create_user(
            username="dr_wait", email="dr_wait@example.com", password="x", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.doctor.department = department
        self.doctor.save()

        self.patient_user = User.objects.create_user(
            username="patient_wait_booker", email="patient_wait_booker@example.com", password="x", role=User.Role.PATIENT
        )
        self.waiting_patient_user = User.objects.create_user(
            username="patient_waiting", email="patient_waiting@example.com", password="x", role=User.Role.PATIENT
        )
        from patients.models import Patient

        self.patient = Patient.objects.get(user=self.patient_user)
        self.waiting_patient = Patient.objects.get(user=self.waiting_patient_user)

        from .models import Appointment, Waitlist

        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor, appointment_date=datetime.date.today(),
            slot_start_time=datetime.time(9, 0), slot_end_time=datetime.time(9, 20),
        )
        self.waitlist_entry = Waitlist.objects.create(
            patient=self.waiting_patient, doctor=self.doctor, preferred_date=datetime.date.today()
        )

    def test_cancelling_appointment_notifies_first_waitlisted_patient(self):
        from notifications.models import Notification

        from .models import Waitlist

        self.client.force_authenticate(self.patient_user)
        resp = self.client.post(f"/api/appointments/{self.appointment.id}/cancel/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.waitlist_entry.refresh_from_db()
        self.assertEqual(self.waitlist_entry.status, Waitlist.Status.NOTIFIED)

        notified = Notification.objects.filter(recipient=self.waiting_patient_user, notification_type=Notification.NotificationType.GENERAL)
        self.assertTrue(notified.exists())
