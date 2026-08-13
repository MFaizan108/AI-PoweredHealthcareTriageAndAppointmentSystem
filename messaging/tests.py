import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from appointments.models import Appointment
from departments.models import Department
from doctors.models import Doctor
from patients.models import Patient


class MessagingPermissionTests(APITestCase):
    def setUp(self):
        dept = Department.objects.create(name="General")
        self.doctor_user = User.objects.create_user(
            username="doc_msg", email="doc_msg@example.com", password="x", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.doctor.department = dept
        self.doctor.save()

        self.patient_user = User.objects.create_user(
            username="pat_msg", email="pat_msg@example.com", password="x", role=User.Role.PATIENT
        )
        self.patient = Patient.objects.get(user=self.patient_user)

        self.outsider = User.objects.create_user(
            username="outsider_msg", email="outsider_msg@example.com", password="x", role=User.Role.PATIENT
        )

        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=datetime.date.today(),
            slot_start_time=datetime.time(10, 0),
            slot_end_time=datetime.time(10, 20),
        )

    def test_patient_can_message_their_appointment_doctor(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post("/api/messages/", {"appointment": self.appointment.id, "body": "Hello doctor"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["recipient"], self.doctor_user.id)

    def test_outsider_cannot_message_into_someone_elses_appointment(self):
        self.client.force_authenticate(self.outsider)
        resp = self.client.post("/api/messages/", {"appointment": self.appointment.id, "body": "Hi"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_see_the_conversation(self):
        self.client.force_authenticate(self.patient_user)
        self.client.post("/api/messages/", {"appointment": self.appointment.id, "body": "Hello doctor"})

        self.client.force_authenticate(self.outsider)
        resp = self.client.get(f"/api/messages/?appointment={self.appointment.id}")
        self.assertEqual(resp.data["count"], 0)

    def test_message_attachment_rejects_disallowed_extension(self):
        self.client.force_authenticate(self.patient_user)
        bad_file = SimpleUploadedFile("script.sh", b"#!/bin/sh\necho hi", content_type="application/octet-stream")
        resp = self.client.post(
            "/api/messages/",
            {"appointment": self.appointment.id, "body": "See attached", "attachment": bad_file},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_message_attachment_accepts_allowed_extension(self):
        self.client.force_authenticate(self.patient_user)
        good_file = SimpleUploadedFile("scan.jpg", b"fake jpeg bytes", content_type="image/jpeg")
        resp = self.client.post(
            "/api/messages/",
            {"appointment": self.appointment.id, "body": "See attached", "attachment": good_file},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)


class MessageAttachmentDownloadTests(APITestCase):
    """attachment must never be reachable via a raw, unauthenticated media URL — same reasoning as
    laboratory.tests.LabReportDownloadTests."""

    def setUp(self):
        dept = Department.objects.create(name="Attachment Dept")
        self.doctor_user = User.objects.create_user(
            username="atc_doc", email="atc_doc@example.com", password="x", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.doctor.department = dept
        self.doctor.save()

        self.patient_user = User.objects.create_user(
            username="atc_pat", email="atc_pat@example.com", password="x", role=User.Role.PATIENT
        )
        self.patient = Patient.objects.get(user=self.patient_user)
        self.outsider = User.objects.create_user(
            username="atc_outsider", email="atc_outsider@example.com", password="x", role=User.Role.PATIENT
        )
        self.admin = User.objects.create_user(
            username="atc_admin", email="atc_admin@example.com", password="x", role=User.Role.ADMIN
        )

        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=datetime.date.today(),
            slot_start_time=datetime.time(10, 0),
            slot_end_time=datetime.time(10, 20),
        )

        self.client.force_authenticate(self.patient_user)
        good_file = SimpleUploadedFile("scan.jpg", b"fake jpeg bytes", content_type="image/jpeg")
        resp = self.client.post(
            "/api/messages/",
            {"appointment": self.appointment.id, "body": "See attached", "attachment": good_file},
            format="multipart",
        )
        self.message_id = resp.data["id"]
        self.client.force_authenticate(None)

    def test_serializer_exposes_download_endpoint_not_raw_media_path(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get(f"/api/messages/{self.message_id}/")
        self.assertEqual(resp.data["attachment"], f"/api/messages/{self.message_id}/attachment/")
        self.assertNotIn("/media/", resp.data["attachment"])

    def test_unauthenticated_request_is_rejected(self):
        resp = self.client.get(f"/api/messages/{self.message_id}/attachment/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sender_and_recipient_can_download(self):
        for user in (self.patient_user, self.doctor_user):
            self.client.force_authenticate(user)
            resp = self.client.get(f"/api/messages/{self.message_id}/attachment/")
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertEqual(b"".join(resp.streaming_content), b"fake jpeg bytes")

    def test_outsider_cannot_download(self):
        self.client.force_authenticate(self.outsider)
        resp = self.client.get(f"/api/messages/{self.message_id}/attachment/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_download(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(f"/api/messages/{self.message_id}/attachment/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
