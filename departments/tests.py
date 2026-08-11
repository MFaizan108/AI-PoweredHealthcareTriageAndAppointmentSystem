from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import Department


class DepartmentPermissionTests(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Cardiology")
        self.admin = User.objects.create_user(username="dept_admin", email="dept_admin@example.com", password="x", role=User.Role.ADMIN)
        self.patient = User.objects.create_user(username="dept_patient", email="dept_patient@example.com", password="x", role=User.Role.PATIENT)

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
