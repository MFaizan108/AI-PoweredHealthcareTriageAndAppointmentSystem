from rest_framework import viewsets

from .models import Invoice, Payment
from .permissions import BILLING_STAFF, CanAccessInvoice, CanAccessPayment
from .serializers import InvoiceSerializer, PaymentSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related("patient__user").prefetch_related("payments")
    serializer_class = InvoiceSerializer
    permission_classes = [CanAccessInvoice]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user.is_superuser or user.role in BILLING_STAFF):
            qs = qs.filter(patient__user=user)
        patient = self.request.query_params.get("patient")
        if patient:
            qs = qs.filter(patient_id=patient)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("invoice__patient__user")
    serializer_class = PaymentSerializer
    permission_classes = [CanAccessPayment]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user.is_superuser or user.role in BILLING_STAFF):
            qs = qs.filter(invoice__patient__user=user)
        invoice = self.request.query_params.get("invoice")
        if invoice:
            qs = qs.filter(invoice_id=invoice)
        return qs

    def perform_create(self, serializer):
        payment = serializer.save(recorded_by=self.request.user)
        invoice = payment.invoice
        if payment.status == Payment.Status.SUCCESS:
            if invoice.amount_paid >= invoice.total_amount and invoice.total_amount > 0:
                invoice.status = Invoice.Status.PAID
            elif invoice.amount_paid > 0:
                invoice.status = Invoice.Status.PARTIALLY_PAID
            invoice.save(update_fields=["status"])
