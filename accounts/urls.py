from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .password_reset import PasswordResetConfirmView, PasswordResetRequestView
from .two_factor import (
    TwoFactorDisableView,
    TwoFactorEnableView,
    TwoFactorRecoveryCodesRegenerateView,
    TwoFactorSetupView,
)
from .verification import ResendVerificationView, VerifyEmailConfirmView
from .views import (
    LoginHistoryView,
    LoginView,
    LogoutAllDevicesView,
    LogoutView,
    MeView,
    ReceptionistPatientRegisterView,
    RegisterView,
    StaffCreateView,
    UserListView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register/patient/", ReceptionistPatientRegisterView.as_view(), name="register_patient_by_staff"),
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("login/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout-all/", LogoutAllDevicesView.as_view(), name="logout_all"),
    path("login-history/", LoginHistoryView.as_view(), name="login_history"),
    path("me/", MeView.as_view(), name="me"),
    path("staff/create/", StaffCreateView.as_view(), name="staff_create"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("2fa/setup/", TwoFactorSetupView.as_view(), name="2fa_setup"),
    path("2fa/enable/", TwoFactorEnableView.as_view(), name="2fa_enable"),
    path("2fa/disable/", TwoFactorDisableView.as_view(), name="2fa_disable"),
    path("2fa/recovery-codes/regenerate/", TwoFactorRecoveryCodesRegenerateView.as_view(), name="2fa_recovery_codes_regenerate"),
    path("verify-email/resend/", ResendVerificationView.as_view(), name="verify_email_resend"),
    path("verify-email/confirm/", VerifyEmailConfirmView.as_view(), name="verify_email_confirm"),
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
