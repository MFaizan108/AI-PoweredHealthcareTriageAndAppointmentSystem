from rest_framework import serializers

from patients.serializers import PatientSerializer

from .models import Invoice, Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "invoice", "amount", "method", "status", "recorded_by", "reference", "created_at"]
        read_only_fields = ["id", "recorded_by", "created_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "patient",
            "patient_detail",
            "appointment",
            "lab_test",
            "description",
            "consultation_fee",
            "lab_charges",
            "discount",
            "total_amount",
            "status",
            "payments",
            "amount_paid",
            "balance_due",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "total_amount", "created_at", "updated_at"]
