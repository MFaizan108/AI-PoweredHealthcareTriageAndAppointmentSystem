from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .tasks import send_account_email
from .token_utils import blacklist_all_outstanding_tokens


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetDetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


@extend_schema(tags=["Accounts"], request=PasswordResetRequestSerializer, responses=PasswordResetDetailResponseSerializer, description="Always returns 200 regardless of whether the email exists, to avoid user enumeration.")
class PasswordResetRequestView(APIView):
    """Always returns 200 regardless of whether the email exists, to avoid user enumeration."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_account_email.delay(
                user.email,
                "Password reset request",
                f"Reset your password by submitting POST /api/accounts/password-reset/confirm/ with:\n"
                f'{{"uid": "{uid}", "token": "{token}", "new_password": "..."}}\n\n'
                "If you did not request this, you can ignore this email.",
            )
        return Response({"detail": "If that email exists, a reset link has been sent."})


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


@extend_schema(tags=["Accounts"], request=PasswordResetConfirmSerializer, responses=PasswordResetDetailResponseSerializer, description="Consumes the uid/token pair from the reset email and sets a new password.")
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            uid = force_str(urlsafe_base64_decode(data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, data["token"]):
            return Response({"detail": "Invalid or expired reset link."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        # A password reset almost always means "I think someone else might have access" — kill every
        # other session's ability to refresh, not just the one making this request.
        blacklist_all_outstanding_tokens(user)
        return Response({"detail": "Password reset successfully."})
