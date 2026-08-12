from django.core import signing
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .tasks import send_account_email

VERIFY_EMAIL_SALT = "accounts.email-verification"
VERIFY_EMAIL_MAX_AGE = 60 * 60 * 24  # 24 hours


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


def _make_verification_token(user):
    return signing.dumps({"user_id": user.id}, salt=VERIFY_EMAIL_SALT)


def send_verification_email(user):
    token = _make_verification_token(user)
    send_account_email.delay(
        user.email,
        "Verify your email",
        f"Verify your account using this token: {token}\n\n"
        f'Submit it to POST /api/accounts/verify-email/confirm/ as {{"token": "..."}}.\n'
        "This link expires in 24 hours.",
    )


@extend_schema(
    tags=["Accounts"],
    request=None,
    responses=DetailResponseSerializer,
    description="Re-sends the account email-verification token to the current user's email address.",
)
class ResendVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.email_verified:
            return Response({"detail": "Email already verified."})
        send_verification_email(request.user)
        return Response({"detail": "Verification email sent."})


class VerifyEmailConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()


@extend_schema(
    tags=["Accounts"],
    request=VerifyEmailConfirmSerializer,
    responses=DetailResponseSerializer,
    description="Confirms the signed token (24h expiry) sent to the user's email and marks the account verified.",
)
class VerifyEmailConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = signing.loads(serializer.validated_data["token"], salt=VERIFY_EMAIL_SALT, max_age=VERIFY_EMAIL_MAX_AGE)
        except signing.SignatureExpired:
            return Response({"detail": "Verification link expired."}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
            return Response({"detail": "Invalid verification token."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=data["user_id"]).first()
        if not user:
            return Response({"detail": "Invalid verification token."}, status=status.HTTP_400_BAD_REQUEST)

        user.email_verified = True
        user.save(update_fields=["email_verified"])
        return Response({"detail": "Email verified successfully."})
