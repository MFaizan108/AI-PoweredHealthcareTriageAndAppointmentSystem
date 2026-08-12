from rest_framework import serializers

from accounts.models import User
from accounts.serializers import UserSerializer

from .models import Doctor, DoctorAvailability, DoctorLeave


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = ["id", "doctor", "weekday", "start_time", "end_time", "slot_duration_minutes", "is_active"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError("end_time must be after start_time.")
        return attrs


class DoctorLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorLeave
        fields = ["id", "doctor", "start_date", "end_date", "reason"]
        read_only_fields = ["id"]


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.DOCTOR), source="user", write_only=True
    )
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Doctor
        fields = [
            "id",
            "user",
            "user_id",
            "department",
            "department_name",
            "specialization",
            "qualification",
            "license_number",
            "experience_years",
            "consultation_fee",
            "bio",
            "is_active",
        ]
        read_only_fields = ["id"]
