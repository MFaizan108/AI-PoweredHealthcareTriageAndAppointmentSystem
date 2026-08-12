from rest_framework import serializers

from doctors.serializers import DoctorSerializer
from patients.serializers import PatientSerializer

from .models import Prescription, PrescriptionItem


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = ["id", "prescription", "medicine_name", "dosage", "frequency", "duration", "instructions"]
        read_only_fields = ["id"]
        extra_kwargs = {"prescription": {"required": False}}


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    doctor_detail = DoctorSerializer(source="doctor", read_only=True)
    items = PrescriptionItemSerializer(many=True, required=False)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "patient",
            "patient_detail",
            "doctor",
            "doctor_detail",
            "appointment",
            "medical_record",
            "notes",
            "items",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        prescription = Prescription.objects.create(**validated_data)
        for item_data in items_data:
            PrescriptionItem.objects.create(prescription=prescription, **item_data)
        return prescription
