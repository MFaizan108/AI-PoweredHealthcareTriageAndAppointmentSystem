from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from patients.models import Patient

from .models import Invoice


class InvoiceTotalTests(TestCase):
    def test_total_amount_is_computed_on_save(self):
        patient_user = User.objects.create_user(username="p1", email="p1@example.com", password="x", role=User.Role.PATIENT)
        patient = Patient.objects.get(user=patient_user)
        invoice = Invoice.objects.create(
            patient=patient,
            description="Consultation",
            consultation_fee=Decimal("1500.00"),
            lab_charges=Decimal("500.00"),
            discount=Decimal("200.00"),
        )
        self.assertEqual(invoice.total_amount, Decimal("1800.00"))

    def test_total_amount_never_negative(self):
        patient_user = User.objects.create_user(username="p2", email="p2@example.com", password="x", role=User.Role.PATIENT)
        patient = Patient.objects.get(user=patient_user)
        invoice = Invoice.objects.create(
            patient=patient,
            description="Consultation",
            consultation_fee=Decimal("100.00"),
            discount=Decimal("500.00"),
        )
        self.assertEqual(invoice.total_amount, Decimal("0.00"))


class PaymentUpdatesInvoiceStatusTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin1", email="admin1@example.com", password="x", role=User.Role.ADMIN, is_staff=True
        )
        patient_user = User.objects.create_user(username="p3", email="p3@example.com", password="x", role=User.Role.PATIENT)
        self.patient = Patient.objects.get(user=patient_user)
        self.invoice = Invoice.objects.create(
            patient=self.patient, description="Consultation", consultation_fee=Decimal("1000.00")
        )

    def test_full_payment_marks_invoice_paid(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            "/api/billing/payments/",
            {"invoice": self.invoice.id, "amount": "1000.00", "method": "cash", "status": "success"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)

    def test_partial_payment_marks_invoice_partially_paid(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            "/api/billing/payments/",
            {"invoice": self.invoice.id, "amount": "400.00", "method": "cash", "status": "success"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PARTIALLY_PAID)

    def test_patient_cannot_record_payments(self):
        self.client.force_authenticate(self.patient.user)
        resp = self.client.post(
            "/api/billing/payments/",
            {"invoice": self.invoice.id, "amount": "1000.00", "method": "cash", "status": "success"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_can_view_own_invoice_but_not_others(self):
        other_user = User.objects.create_user(username="p4", email="p4@example.com", password="x", role=User.Role.PATIENT)
        self.client.force_authenticate(self.patient.user)
        resp = self.client.get("/api/billing/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

        self.client.force_authenticate(other_user)
        resp2 = self.client.get("/api/billing/")
        self.assertEqual(resp2.data["count"], 0)
