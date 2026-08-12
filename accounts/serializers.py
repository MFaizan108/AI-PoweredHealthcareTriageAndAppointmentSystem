import pyotp
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "is_2fa_enabled",
            "email_verified",
            "date_joined",
        ]
        read_only_fields = ["id", "role", "is_2fa_enabled", "email_verified", "date_joined"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds an optional otp_code check on top of the normal username/password check. If the account
    lost access to its authenticator app, a single-use recovery_code can be sent instead of otp_code."""

    otp_code = serializers.CharField(required=False, allow_blank=True, write_only=True)
    recovery_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate(self, attrs):
        otp_code = attrs.pop("otp_code", "")
        recovery_code = attrs.pop("recovery_code", "")
        data = super().validate(attrs)

        if self.user.is_2fa_enabled:
            if recovery_code:
                from .recovery_codes import consume_recovery_code

                if not consume_recovery_code(self.user, recovery_code):
                    raise serializers.ValidationError(
                        {"recovery_code": "Invalid or already-used recovery code."}, code="recovery_code_invalid"
                    )
            elif otp_code:
                totp = pyotp.TOTP(self.user.otp_secret)
                if not totp.verify(otp_code, valid_window=1):
                    raise serializers.ValidationError({"otp_code": "Invalid or expired 2FA code."}, code="2fa_invalid")
            else:
                raise serializers.ValidationError(
                    {"otp_code": "This account has 2FA enabled. Provide otp_code or recovery_code."}, code="2fa_required"
                )

        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name", "role", "phone_number"]

    def validate_role(self, value):
        # Public registration may only self-register as a patient.
        # Staff roles (doctor/receptionist/lab_staff/admin) must be created by an admin.
        if value and value != User.Role.PATIENT:
            raise serializers.ValidationError("Self-registration is only allowed for the patient role.")
        return value

    def create(self, validated_data):
        from .verification import send_verification_email

        validated_data.setdefault("role", User.Role.PATIENT)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        send_verification_email(user)
        return user


class StaffCreateSerializer(serializers.ModelSerializer):
    """Used by admins to create doctor/receptionist/lab_staff/admin accounts."""

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name", "role", "phone_number"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
