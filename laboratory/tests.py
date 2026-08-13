from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from doctors.models import Doctor
from patients.models import Patient

from .models import LabTest


class LabTestWorkflowTests(APITestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username="lab_doc", email="lab_doc@example.com", password="x", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()

        self.other_doctor_user = User.objects.create_user(
            username="lab_doc2", email="lab_doc2@example.com", password="x", role=User.Role.DOCTOR
        )

        self.patient_user = User.objects.create_user(
            username="lab_pat", email="lab_pat@example.com", password="x", role=User.Role.PATIENT
        )
        self.patient = Patient.objects.get(user=self.patient_user)
        self.other_patient_user = User.objects.create_user(
            username="lab_pat2", email="lab_pat2@example.com", password="x", role=User.Role.PATIENT
        )

        self.lab_staff = User.objects.create_user(
            username="lab_staff1", email="lab_staff1@example.com", password="x", role=User.Role.LAB_STAFF
        )
        self.receptionist = User.objects.create_user(
            username="lab_recep", email="lab_recep@example.com", password="x", role=User.Role.RECEPTIONIST
        )

        self.lab_test = LabTest.objects.create(patient=self.patient, requested_by=self.doctor, test_name="Complete Blood Count")

    def test_doctor_can_request_lab_test(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post("/api/lab/", {"patient": self.patient.id, "test_name": "Lipid Profile"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["requested_by"], self.doctor.id)

    def test_patient_cannot_request_lab_test(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.post("/api/lab/", {"patient": self.patient.id, "test_name": "Lipid Profile"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_receptionist_has_no_access_to_lab_tests(self):
        self.client.force_authenticate(self.receptionist)
        resp = self.client.get("/api/lab/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_lab_staff_sees_all_lab_tests(self):
        self.client.force_authenticate(self.lab_staff)
        resp = self.client.get("/api/lab/")
        self.assertEqual(resp.data["count"], 1)

    def test_non_requesting_doctor_cannot_view_test(self):
        self.client.force_authenticate(self.other_doctor_user)
        resp = self.client.get(f"/api/lab/{self.lab_test.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_cannot_see_another_patients_lab_test(self):
        self.client.force_authenticate(self.other_patient_user)
        resp = self.client.get(f"/api/lab/{self.lab_test.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_lab_tests_by_status(self):
        LabTest.objects.create(patient=self.patient, requested_by=self.doctor, test_name="X-Ray", status=LabTest.Status.COMPLETED)
        self.client.force_authenticate(self.lab_staff)
        resp = self.client.get("/api/lab/?status=completed")
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["test_name"], "X-Ray")


class LabReportTests(APITestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username="rep_doc", email="rep_doc@example.com", password="x", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.patient_user = User.objects.create_user(
            username="rep_pat", email="rep_pat@example.com", password="x", role=User.Role.PATIENT
        )
        self.patient = Patient.objects.get(user=self.patient_user)
        self.lab_staff = User.objects.create_user(
            username="rep_lab", email="rep_lab@example.com", password="x", role=User.Role.LAB_STAFF
        )

        self.lab_test = LabTest.objects.create(patient=self.patient, requested_by=self.doctor, test_name="Thyroid Panel")

    def test_lab_staff_can_upload_report_and_test_marked_completed(self):
        self.client.force_authenticate(self.lab_staff)
        resp = self.client.post("/api/lab/reports/", {"lab_test": self.lab_test.id, "result_summary": "All values normal."})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        self.lab_test.refresh_from_db()
        self.assertEqual(self.lab_test.status, LabTest.Status.COMPLETED)

    def test_doctor_cannot_upload_report(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.post("/api/lab/reports/", {"lab_test": self.lab_test.id, "result_summary": "Normal"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_report_upload_notifies_patient_and_requesting_doctor(self):
        from notifications.models import Notification

        self.client.force_authenticate(self.lab_staff)
        self.client.post("/api/lab/reports/", {"lab_test": self.lab_test.id, "result_summary": "Normal"})

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.patient_user, notification_type=Notification.NotificationType.LAB_REPORT_AVAILABLE
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.doctor_user, notification_type=Notification.NotificationType.LAB_REPORT_AVAILABLE
            ).exists()
        )

    def test_patient_can_view_own_report(self):
        from .models import LabReport

        LabReport.objects.create(lab_test=self.lab_test, result_summary="Normal", uploaded_by=self.lab_staff)
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get("/api/lab/reports/")
        self.assertEqual(resp.data["count"], 1)

    def test_report_upload_rejects_disallowed_file_extension(self):
        self.client.force_authenticate(self.lab_staff)
        bad_file = SimpleUploadedFile("malware.exe", b"not a real report", content_type="application/octet-stream")
        resp = self.client.post(
            "/api/lab/reports/",
            {"lab_test": self.lab_test.id, "report_file": bad_file},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_report_upload_accepts_pdf(self):
        self.client.force_authenticate(self.lab_staff)
        good_file = SimpleUploadedFile("report.pdf", b"%PDF-1.4 fake pdf content", content_type="application/pdf")
        resp = self.client.post(
            "/api/lab/reports/",
            {"lab_test": self.lab_test.id, "report_file": good_file},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)


class LabReportDownloadTests(APITestCase):
    """report_file must never be reachable via a raw, unauthenticated media URL — every download
    goes through this endpoint, gated by the same rule as viewing the report resource itself."""

    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username="dl_doc", email="dl_doc@example.com", password="x", role=User.Role.DOCTOR
        )
        self.doctor = Doctor.objects.filter(user=self.doctor_user).first()
        self.other_doctor_user = User.objects.create_user(
            username="dl_doc2", email="dl_doc2@example.com", password="x", role=User.Role.DOCTOR
        )
        self.patient_user = User.objects.create_user(
            username="dl_pat", email="dl_pat@example.com", password="x", role=User.Role.PATIENT
        )
        self.patient = Patient.objects.get(user=self.patient_user)
        self.other_patient_user = User.objects.create_user(
            username="dl_pat2", email="dl_pat2@example.com", password="x", role=User.Role.PATIENT
        )
        self.lab_staff = User.objects.create_user(
            username="dl_lab", email="dl_lab@example.com", password="x", role=User.Role.LAB_STAFF
        )
        self.admin = User.objects.create_user(
            username="dl_admin", email="dl_admin@example.com", password="x", role=User.Role.ADMIN
        )

        self.lab_test = LabTest.objects.create(patient=self.patient, requested_by=self.doctor, test_name="Thyroid Panel")

        from .models import LabReport

        pdf = SimpleUploadedFile("report.pdf", b"%PDF-1.4 fake pdf content", content_type="application/pdf")
        self.report = LabReport.objects.create(lab_test=self.lab_test, report_file=pdf, uploaded_by=self.lab_staff)

    def test_serializer_exposes_download_endpoint_not_raw_media_path(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get("/api/lab/reports/")
        report_file_url = resp.data["results"][0]["report_file"]
        self.assertEqual(report_file_url, f"/api/lab/reports/{self.report.id}/download/")
        self.assertNotIn("/media/", report_file_url)

    def test_unauthenticated_request_is_rejected(self):
        resp = self.client.get(f"/api/lab/reports/{self.report.id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owning_patient_can_download(self):
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get(f"/api/lab/reports/{self.report.id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(resp.streaming_content), b"%PDF-1.4 fake pdf content")

    def test_another_patient_cannot_download(self):
        self.client.force_authenticate(self.other_patient_user)
        resp = self.client.get(f"/api/lab/reports/{self.report.id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_requesting_doctor_can_download_but_another_doctor_cannot(self):
        self.client.force_authenticate(self.doctor_user)
        resp = self.client.get(f"/api/lab/reports/{self.report.id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.other_doctor_user)
        resp = self.client.get(f"/api/lab/reports/{self.report.id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_lab_staff_and_admin_can_always_download(self):
        for user in (self.lab_staff, self.admin):
            self.client.force_authenticate(user)
            resp = self.client.get(f"/api/lab/reports/{self.report.id}/download/")
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_report_with_no_file_returns_404(self):
        from .models import LabReport

        other_test = LabTest.objects.create(patient=self.patient, requested_by=self.doctor, test_name="X-Ray")
        empty_report = LabReport.objects.create(lab_test=other_test, uploaded_by=self.lab_staff)
        self.client.force_authenticate(self.patient_user)
        resp = self.client.get(f"/api/lab/reports/{empty_report.id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class MaxFileSizeValidatorTests(APITestCase):
    def test_rejects_file_over_the_limit(self):
        from django.core.exceptions import ValidationError

        from ai_healthcare_triage_appointment_system.validators import MaxFileSizeValidator

        validator = MaxFileSizeValidator(max_mb=1)
        oversized = SimpleUploadedFile("big.pdf", b"x" * (2 * 1024 * 1024))
        with self.assertRaises(ValidationError):
            validator(oversized)

    def test_allows_file_under_the_limit(self):
        from ai_healthcare_triage_appointment_system.validators import MaxFileSizeValidator

        validator = MaxFileSizeValidator(max_mb=1)
        small = SimpleUploadedFile("small.pdf", b"x" * 1024)
        validator(small)  # must not raise
