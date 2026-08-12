from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import AuditLog

TEST_OVERRIDES = dict(
    CELERY_TASK_ALWAYS_EAGER=True, MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
)


@override_settings(**TEST_OVERRIDES)
class AuditLogMiddlewareTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user(
            username="audit_admin", email="audit_admin@example.com", password="x", role=User.Role.ADMIN
        )
        self.patient = User.objects.create_user(
            username="audit_pat", email="audit_pat@example.com", password="x", role=User.Role.PATIENT
        )

    def test_mutating_request_is_logged(self):
        self.client.force_authenticate(self.patient)
        self.client.post("/api/departments/", {"name": "Should Fail But Still Logged"})
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.patient, action=AuditLog.Action.REQUEST, method="POST", path="/api/departments/"
            ).exists()
        )

    def test_get_request_is_not_logged(self):
        self.client.force_authenticate(self.patient)
        before = AuditLog.objects.count()
        self.client.get("/api/departments/")
        after = AuditLog.objects.count()
        self.assertEqual(before, after)

    def test_failed_login_is_logged_with_attempted_username_and_no_user(self):
        self.client.post("/api/accounts/login/", {"username": "audit_pat", "password": "wrong-password"})
        entry = AuditLog.objects.filter(action=AuditLog.Action.LOGIN_FAILED, username_attempted="audit_pat").first()
        self.assertIsNotNone(entry)
        self.assertIsNone(entry.user)

    def test_successful_login_is_logged_with_resolved_user(self):
        self.client.post("/api/accounts/login/", {"username": "audit_pat", "password": "x"})
        entry = AuditLog.objects.filter(action=AuditLog.Action.LOGIN_SUCCESS, user=self.patient).first()
        self.assertIsNotNone(entry)

    def test_object_id_is_extracted_from_the_url_path(self):
        self.client.force_authenticate(self.admin)
        self.client.patch("/api/departments/999/", {"name": "Renamed"}, format="json")
        entry = AuditLog.objects.filter(method="PATCH", path="/api/departments/999/").first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.object_id, "999")

    def test_request_body_is_captured_as_changes(self):
        self.client.force_authenticate(self.admin)
        self.client.post("/api/departments/", {"name": "Radiology"}, format="json")
        entry = AuditLog.objects.filter(method="POST", path="/api/departments/").first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.changes.get("name"), "Radiology")

    def test_sensitive_fields_are_redacted_in_changes(self):
        self.client.force_authenticate(self.admin)
        self.client.post(
            "/api/accounts/staff/create/",
            {
                "username": "newstaffmember",
                "email": "newstaffmember@example.com",
                "password": "SuperSecret123!",
                "role": "doctor",
            },
            format="json",
        )
        entry = AuditLog.objects.filter(method="POST", path="/api/accounts/staff/create/").first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.changes.get("password"), "***REDACTED***")
        self.assertEqual(entry.changes.get("username"), "newstaffmember")


@override_settings(**TEST_OVERRIDES)
class AuditLogAccessTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="audit_admin2", email="audit_admin2@example.com", password="x", role=User.Role.ADMIN
        )
        self.patient = User.objects.create_user(
            username="audit_pat2", email="audit_pat2@example.com", password="x", role=User.Role.PATIENT
        )
        self.doctor = User.objects.create_user(
            username="audit_doc", email="audit_doc@example.com", password="x", role=User.Role.DOCTOR
        )

    def test_admin_can_read_audit_log(self):
        AuditLog.objects.create(action=AuditLog.Action.REQUEST, method="POST", path="/api/x/", status_code=201)
        self.client.force_authenticate(self.admin)
        resp = self.client.get("/api/audit-logs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data["count"], 1)

    def test_non_admin_cannot_read_audit_log(self):
        self.client.force_authenticate(self.patient)
        resp = self.client.get("/api/audit-logs/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_cannot_read_audit_log(self):
        self.client.force_authenticate(self.doctor)
        resp = self.client.get("/api/audit-logs/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_read_audit_log(self):
        resp = self.client.get("/api/audit-logs/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
