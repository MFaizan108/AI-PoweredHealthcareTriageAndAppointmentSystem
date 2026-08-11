import pyotp
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class TwoFactorSetupResponseSerializer(serializers.Serializer):
    secret = serializers.CharField()
    provisioning_uri = serializers.CharField()


@extend_schema(
    tags=["Accounts"],
    request=None,
    responses=TwoFactorSetupResponseSerializer,
    description="Generates (or regenerates) a TOTP secret for the current user. Not yet enabled — "
    "the user must confirm a code via POST /2fa/enable/ before it takes effect on login.",
)
class TwoFactorSetupView(APIView):
    """Generates (or regenerates) a TOTP secret for the current user. Not yet enabled —
    the user must confirm a code via TwoFactorEnableView before it takes effect on login."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        secret = pyotp.random_base32()
        user.otp_secret = secret
        user.is_2fa_enabled = False
        user.save(update_fields=["otp_secret", "is_2fa_enabled"])

        provisioning_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email or user.username, issuer_name="AI Healthcare Triage")
        return Response({"secret": secret, "provisioning_uri": provisioning_uri})


class TwoFactorEnableSerializer(serializers.Serializer):
    otp_code = serializers.CharField()


class TwoFactorStatusResponseSerializer(serializers.Serializer):
    is_2fa_enabled = serializers.BooleanField()


@extend_schema(tags=["Accounts"], request=TwoFactorEnableSerializer, responses=TwoFactorStatusResponseSerializer, description="Confirms a TOTP code from an authenticator app and turns 2FA on for the account.")
class TwoFactorEnableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.otp_secret:
            return Response({"detail": "Call /2fa/setup/ first."}, status=status.HTTP_400_BAD_REQUEST)

        totp = pyotp.TOTP(user.otp_secret)
        if not totp.verify(serializer.validated_data["otp_code"], valid_window=1):
            return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = True
        user.save(update_fields=["is_2fa_enabled"])
        return Response({"is_2fa_enabled": True})


class TwoFactorDisableSerializer(serializers.Serializer):
    password = serializers.CharField()


@extend_schema(tags=["Accounts"], request=TwoFactorDisableSerializer, responses=TwoFactorStatusResponseSerializer, description="Disables 2FA for the current account after confirming the account password.")
class TwoFactorDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["password"]):
            return Response({"detail": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_2fa_enabled = False
        user.otp_secret = ""
        user.save(update_fields=["is_2fa_enabled", "otp_secret"])
        return Response({"is_2fa_enabled": False})
