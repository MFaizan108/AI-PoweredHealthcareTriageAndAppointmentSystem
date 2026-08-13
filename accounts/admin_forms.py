import pyotp
from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm


class TwoFactorAdminAuthenticationForm(AdminAuthenticationForm):
    """Django's stock admin login only knows username/password — without this, /admin/ was a
    second login surface that completely bypassed the app's 2FA requirement, since the JWT-based
    API login (accounts.serializers.CustomTokenObtainPairSerializer) is the only place that ever
    checked `is_2fa_enabled`/`otp_secret`. An account with 2FA enabled had it silently skipped
    just by using /admin/ instead of the app's own login form."""

    otp_code = forms.CharField(
        label="Authenticator code",
        required=False,
        help_text="Only required if two-factor authentication is enabled on this account.",
    )

    def clean(self):
        cleaned_data = super().clean()
        user = self.get_user()
        if user is not None and getattr(user, "is_2fa_enabled", False):
            code = (cleaned_data.get("otp_code") or "").strip()
            if not code or not pyotp.TOTP(user.otp_secret).verify(code, valid_window=1):
                raise forms.ValidationError("Invalid or missing authenticator code.", code="invalid_otp")
        return cleaned_data
