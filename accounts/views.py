from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import IsAdmin, IsAdminOrReceptionist
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, StaffCreateSerializer, UserSerializer
from .throttles import LoginRateThrottle


@extend_schema(tags=["Accounts"])
class LoginView(TokenObtainPairView):
    """Same as TokenObtainPairView, but rate-limited (5/minute) and 2FA-aware
    (see CustomTokenObtainPairSerializer — pass `otp_code` if 2FA is enabled)."""

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]
    throttle_scope = "login"


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


@extend_schema(
    tags=["Accounts"],
    request=LogoutSerializer,
    responses={205: None, 400: OpenApiResponse(description="Invalid or already-blacklisted refresh token")},
    description="Blacklists the given refresh token so it can no longer be used to obtain new access tokens.",
)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Invalid or already-blacklisted token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


@extend_schema(tags=["Accounts"], description="Public self-registration — always creates a `patient` account; the `role` field, if sent, is ignored.")
class RegisterView(generics.CreateAPIView):
    """Public self-registration — patients only."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=["Accounts"], description="Admin/receptionist-facing walk-in patient registration (forces role=patient).")
class ReceptionistPatientRegisterView(generics.CreateAPIView):
    """Admin/receptionist-facing walk-in patient registration (forces role=patient)."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAdminOrReceptionist]


@extend_schema(tags=["Accounts"], description="Admin-only endpoint to create doctor/receptionist/lab_staff/admin accounts.")
class StaffCreateView(generics.CreateAPIView):
    """Admin-only endpoint to create doctor/receptionist/lab_staff/admin accounts."""

    queryset = User.objects.all()
    serializer_class = StaffCreateSerializer
    permission_classes = [IsAdmin]


@extend_schema(tags=["Accounts"], responses=UserSerializer, description="Returns the currently authenticated user's profile.")
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


@extend_schema(tags=["Accounts"], description="Admin-only: list all users, optionally filtered by `?role=`.")
class UserListView(generics.ListAPIView):
    """Admin-only: list all users, optionally filtered by role."""

    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs


class LoginHistoryEntrySerializer(serializers.Serializer):
    ip_address = serializers.CharField(allow_null=True)
    user_agent = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()


@extend_schema(tags=["Accounts"], responses=LoginHistoryEntrySerializer(many=True), description="Self-service: the current user's own successful-login history (device/IP/time), most recent 50.")
class LoginHistoryView(APIView):
    """Self-service: the current user's own successful-login history (device/IP/time)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from audit_logs.models import AuditLog

        entries = AuditLog.objects.filter(
            user=request.user, action=AuditLog.Action.LOGIN_SUCCESS
        ).order_by("-created_at")[:50]
        return Response([
            {"ip_address": e.ip_address, "user_agent": e.user_agent, "created_at": e.created_at}
            for e in entries
        ])
