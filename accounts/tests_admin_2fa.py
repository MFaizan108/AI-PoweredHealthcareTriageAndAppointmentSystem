import pyotp
from django.test import TestCase
from django.urls import reverse

from .models import User


class AdminTwoFactorLoginTests(TestCase):
    """/admin/ is a second login surface Django provides for free — without
    accounts.admin_forms.TwoFactorAdminAuthenticationForm wired in, it completely bypassed the
    app's 2FA requirement, since Django's stock admin login only ever checks username/password."""

    def setUp(self):
        self.password = "AdminPass123!"

    def _create_admin(self, username, with_2fa=False):
        user = User.objects.create_superuser(username=username, email=f"{username}@example.com", password=self.password)
        secret = None
        if with_2fa:
            secret = pyotp.random_base32()
            user.otp_secret = secret
            user.is_2fa_enabled = True
            user.save(update_fields=["otp_secret", "is_2fa_enabled"])
        return user, secret

    def _attempt_login(self, username, otp_code=""):
        return self.client.post(
            reverse("admin:login"), {"username": username, "password": self.password, "otp_code": otp_code, "next": "/admin/"}
        )

    def _is_logged_in(self):
        return self.client.get(reverse("admin:index")).status_code == 200

    def test_account_without_2fa_logs_in_with_password_only(self):
        self._create_admin("plain_admin")
        self._attempt_login("plain_admin")
        self.assertTrue(self._is_logged_in())

    def test_account_with_2fa_cannot_log_in_with_password_only(self):
        self._create_admin("twofa_admin", with_2fa=True)
        self._attempt_login("twofa_admin")
        self.assertFalse(self._is_logged_in())

    def test_account_with_2fa_logs_in_with_a_valid_otp_code(self):
        _, secret = self._create_admin("twofa_admin2", with_2fa=True)
        self._attempt_login("twofa_admin2", otp_code=pyotp.TOTP(secret).now())
        self.assertTrue(self._is_logged_in())

    def test_account_with_2fa_rejects_an_invalid_otp_code(self):
        self._create_admin("twofa_admin3", with_2fa=True)
        self._attempt_login("twofa_admin3", otp_code="000000")
        self.assertFalse(self._is_logged_in())
