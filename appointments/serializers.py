from django.db import IntegrityError
from rest_framework import serializers

from accounts.models import User
from doctors.serializers import DoctorSerializer
from patients.serializers import PatientSerializer

from .models import Appointment, Feedback, Waitlist
from .services import generate_token_number, get_available_slots


class AppointmentSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    doctor_detail = DoctorSerializer(source="doctor", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_detail",
            "doctor",
            "doctor_detail",
            "appointment_date",
            "slot_start_time",
            "slot_end_time",
            "status",
            "reason",
            "token_number",
            "booked_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slot_end_time", "token_number", "booked_by", "created_at", "updated_at"]
        extra_kwargs = {"patient": {"required": False}}

    def validate(self, attrs):
        request = self.context.get("request")
        is_create = self.instance is None

        # A patient's own `patient` link is injected in the view; staff must supply it explicitly.
        if is_create and request and request.user.role != User.Role.PATIENT and "patient" not in attrs:
            raise serializers.ValidationError({"patient": "This field is required."})

        doctor = attrs.get("doctor", getattr(self.instance, "doctor", None))
        date = attrs.get("appointment_date", getattr(self.instance, "appointment_date", None))
        start = attrs.get("slot_start_time", getattr(self.instance, "slot_start_time", None))

        slot_fields_touched = {"doctor", "appointment_date", "slot_start_time"} & set(attrs.keys())

        if is_create or slot_fields_touched:
            slots = get_available_slots(doctor, date)
            match = next((s for s in slots if s["start_time"] == start), None)
            if match is None:
                raise serializers.ValidationError("Requested slot is not a valid slot for this doctor on this date.")
            if not match["available"] and not (self.instance and self.instance.slot_start_time == start):
                raise serializers.ValidationError("This slot is already booked. Please choose another slot.")
            attrs["slot_end_time"] = match["end_time"]

        return attrs

    def create(self, validated_data):
        validated_data["token_number"] = generate_token_number(validated_data["doctor"], validated_data["appointment_date"])
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError("This slot was just booked by someone else. Please choose another slot.")


class AvailableSlotSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    available = serializers.BooleanField()


class WaitlistSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    doctor_detail = DoctorSerializer(source="doctor", read_only=True)

    class Meta:
        model = Waitlist
        fields = ["id", "patient", "patient_detail", "doctor", "doctor_detail", "preferred_date", "status", "notes", "created_at"]
        read_only_fields = ["id", "status", "created_at"]
        extra_kwargs = {"patient": {"required": False}}


class FeedbackSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    doctor_detail = DoctorSerializer(source="doctor", read_only=True)

    class Meta:
        model = Feedback
        fields = ["id", "appointment", "patient", "patient_detail", "doctor", "doctor_detail", "rating", "comment", "created_at"]
        read_only_fields = ["id", "patient", "doctor", "created_at"]

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_appointment(self, appointment):
        if appointment.status != Appointment.Status.COMPLETED:
            raise serializers.ValidationError("Feedback can only be left for a completed appointment.")
        return appointment
