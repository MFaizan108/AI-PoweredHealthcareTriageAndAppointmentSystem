from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id", "user", "date_of_birth", "gender", "blood_group", "address",
            "emergency_contact_name", "emergency_contact_phone", "known_allergies",
        ]
        read_only_fields = ["id"]
