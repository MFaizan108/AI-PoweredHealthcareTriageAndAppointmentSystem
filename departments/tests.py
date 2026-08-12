from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import Department
from .views import LIST_CACHE_KEY


class DepartmentPermissionTests(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Cardiology")
        self.admin = User.objects.create_user(
            username="dept_admin", email="dept_admin@example.com", password="x", role=User.Role.ADMIN
        )
        self.patient = User.objects.create_user(
            username="dept_patient", email="dept_patient@example.com", password="x", role=User.Role.PATIENT
        )

    def test_authenticated_user_can_list_departments(self):
        self.client.force_authenticate(self.patient)
        resp = self.client.get("/api/departments/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_anonymous_user_cannot_list_departments(self):
        resp = self.client.get("/api/departments/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patient_cannot_create_department(self):
        self.client.force_authenticate(self.patient)
        resp = self.client.post("/api/departments/", {"name": "Neurology"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_department(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post("/api/departments/", {"name": "Neurology"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

    def test_department_name_must_be_unique(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post("/api/departments/", {"name": "Cardiology"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class DepartmentListCacheTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user(
            username="dept_cache_admin", email="dept_cache_admin@example.com", password="x", role=User.Role.ADMIN
        )

    def test_list_populates_cache_and_new_department_invalidates_it(self):
        Department.objects.create(name="Radiology")
        self.client.force_authenticate(self.admin)

        first = self.client.get("/api/departments/")
        self.assertEqual(first.data["count"], 1)
        self.assertIsNotNone(cache.get(LIST_CACHE_KEY))

        # A direct model create (bypassing the API, e.g. via admin) must still bust the cache via the signal.
        Department.objects.create(name="Urology")
        self.assertIsNone(cache.get(LIST_CACHE_KEY))

        second = self.client.get("/api/departments/")
        self.assertEqual(second.data["count"], 2)

    def test_cached_list_is_served_without_hitting_the_database_again(self):
        Department.objects.create(name="Oncology")
        self.client.force_authenticate(self.admin)
        self.client.get("/api/departments/")  # warms the cache

        with self.assertNumQueries(0):
            cached_data = cache.get(LIST_CACHE_KEY)
        self.assertEqual(len(cached_data), 1)


class CORSHeaderTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="cors_admin", email="cors_admin@example.com", password="x", role=User.Role.ADMIN
        )

    def test_no_origins_trusted_by_default(self):
        resp = self.client.get("/api/departments/", HTTP_ORIGIN="https://evil.example.com", HTTP_AUTHORIZATION=self._bearer())
        self.assertNotIn("Access-Control-Allow-Origin", resp)

    @override_settings(CORS_ALLOWED_ORIGINS=["https://app.example.com"])
    def test_allow_listed_origin_gets_the_header(self):
        resp = self.client.get("/api/departments/", HTTP_ORIGIN="https://app.example.com", HTTP_AUTHORIZATION=self._bearer())
        self.assertEqual(resp["Access-Control-Allow-Origin"], "https://app.example.com")

    @override_settings(CORS_ALLOWED_ORIGINS=["https://app.example.com"])
    def test_non_allow_listed_origin_does_not_get_the_header(self):
        resp = self.client.get("/api/departments/", HTTP_ORIGIN="https://evil.example.com", HTTP_AUTHORIZATION=self._bearer())
        self.assertNotIn("Access-Control-Allow-Origin", resp)

    def _bearer(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        return f"Bearer {RefreshToken.for_user(self.admin).access_token}"


class SecurityHeaderTests(APITestCase):
    def test_content_security_policy_header_is_present(self):
        resp = self.client.get("/api/docs/")
        self.assertIn("Content-Security-Policy", resp)
        self.assertIn("default-src 'self'", resp["Content-Security-Policy"])

    def test_x_content_type_options_header_is_present(self):
        resp = self.client.get("/api/docs/")
        self.assertEqual(resp.get("X-Content-Type-Options"), "nosniff")
