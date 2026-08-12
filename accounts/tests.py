import pyotp
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User

TEST_OVERRIDES = dict(
    CELERY_TASK_ALWAYS_EAGER=True,
    MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}},
)


@override_settings(**TEST_OVERRIDES)
class RegistrationTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_public_registration_defaults_to_patient(self):
        resp = self.client.post(
            "/api/accounts/register/",
            {"username": "newpatient", "email": "newpatient@example.com", "password": "SomePass123!"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["role"], "patient")

    def test_new_user_is_not_email_verified_until_confirmed(self):
        self.client.post(
            "/api/accounts/register/",
            {"username": "unverified", "email": "unverified@example.com", "password": "SomePass123!"},
        )
        user = User.objects.get(username="unverified")
        self.assertFalse(user.email_verified)

    def test_public_registration_cannot_self_assign_admin_role(self):
        resp = self.client.post(
            "/api/accounts/register/",
            {"username": "sneaky", "email": "sneaky@example.com", "password": "SomePass123!", "role": "admin"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAndTwoFactorTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="loginuser", email="loginuser@example.com", password="LoginPass123!", role=User.Role.PATIENT
        )

    def test_login_returns_access_and_refresh_tokens(self):
        resp = self.client.post("/api/accounts/login/", {"username": "loginuser", "password": "LoginPass123!"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_2fa_setup_enable_and_enforced_login(self):
        self.client.force_authenticate(self.user)
        setup = self.client.post("/api/accounts/2fa/setup/")
        self.assertEqual(setup.status_code, status.HTTP_200_OK)
        secret = setup.data["secret"]

        valid_code = pyotp.TOTP(secret).now()
        enable = self.client.post("/api/accounts/2fa/enable/", {"otp_code": valid_code})
        self.assertEqual(enable.status_code, status.HTTP_200_OK)
        self.assertTrue(enable.data["is_2fa_enabled"])

        self.client.force_authenticate(None)

        without_otp = self.client.post("/api/accounts/login/", {"username": "loginuser", "password": "LoginPass123!"})
        self.assertEqual(without_otp.status_code, status.HTTP_400_BAD_REQUEST)

        fresh_code = pyotp.TOTP(secret).now()
        with_otp = self.client.post(
            "/api/accounts/login/", {"username": "loginuser", "password": "LoginPass123!", "otp_code": fresh_code}
        )
        self.assertEqual(with_otp.status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh_token(self):
        login = self.client.post("/api/accounts/login/", {"username": "loginuser", "password": "LoginPass123!"})
        access, refresh = login.data["access"], login.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout = self.client.post("/api/accounts/logout/", {"refresh": refresh})
        self.assertEqual(logout.status_code, status.HTTP_205_RESET_CONTENT)

        refresh_attempt = self.client.post("/api/accounts/login/refresh/", {"refresh": refresh})
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_returns_a_new_access_token(self):
        login = self.client.post("/api/accounts/login/", {"username": "loginuser", "password": "LoginPass123!"})
        refresh = login.data["refresh"]

        resp = self.client.post("/api/accounts/login/refresh/", {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertNotEqual(resp.data["access"], login.data["access"])

    def test_reusing_a_rotated_refresh_token_is_rejected(self):
        """ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION means a used-once refresh token can't be replayed."""
        login = self.client.post("/api/accounts/login/", {"username": "loginuser", "password": "LoginPass123!"})
        old_refresh = login.data["refresh"]

        first_use = self.client.post("/api/accounts/login/refresh/", {"refresh": old_refresh})
        self.assertEqual(first_use.status_code, status.HTTP_200_OK)

        replay_attempt = self.client.post("/api/accounts/login/refresh/", {"refresh": old_refresh})
        self.assertEqual(replay_attempt.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_already_blacklisted_token_returns_clean_400_not_500(self):
        login = self.client.post("/api/accounts/login/", {"username": "loginuser", "password": "LoginPass123!"})
        access, refresh = login.data["access"], login.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        self.client.post("/api/accounts/logout/", {"refresh": refresh})
        second_logout = self.client.post("/api/accounts/logout/", {"refresh": refresh})
        self.assertEqual(second_logout.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_request_to_protected_endpoint_is_rejected(self):
        resp = self.client.get("/api/accounts/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patient_cannot_create_staff_account(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            "/api/accounts/staff/create/",
            {"username": "sneaky_staff", "email": "sneaky_staff@example.com", "password": "SomePass123!", "role": "doctor"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class LoginRateLimitTests(APITestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(
            username="throttleuser", email="throttleuser@example.com", password="ThrottlePass123!", role=User.Role.PATIENT
        )

    def test_login_is_rate_limited_after_5_attempts_per_minute(self):
        for _ in range(5):
            resp = self.client.post("/api/accounts/login/", {"username": "throttleuser", "password": "wrong"})
            self.assertNotEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        sixth = self.client.post("/api/accounts/login/", {"username": "throttleuser", "password": "wrong"})
        self.assertEqual(sixth.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


@override_settings(**TEST_OVERRIDES)
class EmailVerificationTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_verify_email_with_token_from_registration(self):
        from django.core import signing

        from .verification import VERIFY_EMAIL_SALT

        self.client.post(
            "/api/accounts/register/",
            {"username": "toverify", "email": "toverify@example.com", "password": "SomePass123!"},
        )
        user = User.objects.get(username="toverify")
        token = signing.dumps({"user_id": user.id}, salt=VERIFY_EMAIL_SALT)

        resp = self.client.post("/api/accounts/verify-email/confirm/", {"token": token})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.email_verified)

    def test_invalid_token_rejected(self):
        resp = self.client.post("/api/accounts/verify-email/confirm/", {"token": "not-a-real-token"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(**TEST_OVERRIDES)
class PasswordResetTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="resetme", email="resetme@example.com", password="OldPass123!", role=User.Role.PATIENT
        )

    def test_reset_request_never_reveals_whether_email_exists(self):
        resp_real = self.client.post("/api/accounts/password-reset/request/", {"email": "resetme@example.com"})
        resp_fake = self.client.post("/api/accounts/password-reset/request/", {"email": "nobody@example.com"})
        self.assertEqual(resp_real.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_fake.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_real.data, resp_fake.data)

    def test_confirm_with_valid_token_changes_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        resp = self.client.post(
            "/api/accounts/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "BrandNewPass456!"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        login = self.client.post("/api/accounts/login/", {"username": "resetme", "password": "BrandNewPass456!"})
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_confirm_with_invalid_token_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        resp = self.client.post(
            "/api/accounts/password-reset/confirm/",
            {"uid": uid, "token": "bad-token", "new_password": "BrandNewPass456!"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_blacklists_all_outstanding_refresh_tokens(self):
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        from rest_framework_simplejwt.tokens import RefreshToken

        old_refresh = RefreshToken.for_user(self.user)
        self.assertTrue(OutstandingToken.objects.filter(jti=old_refresh["jti"]).exists())
        self.assertFalse(BlacklistedToken.objects.filter(token__jti=old_refresh["jti"]).exists())

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        self.client.post(
            "/api/accounts/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "BrandNewPass456!"},
        )

        self.assertTrue(BlacklistedToken.objects.filter(token__jti=old_refresh["jti"]).exists())
        refresh_attempt = self.client.post("/api/accounts/login/refresh/", {"refresh": str(old_refresh)})
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(**TEST_OVERRIDES)
class LogoutAllDevicesTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="multidevice", email="multidevice@example.com", password="MultiDevice123!", role=User.Role.PATIENT
        )

    def test_logout_all_blacklists_every_outstanding_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        session1 = self.client.post("/api/accounts/login/", {"username": "multidevice", "password": "MultiDevice123!"})
        session2_refresh = RefreshToken.for_user(self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {session1.data['access']}")
        resp = self.client.post("/api/accounts/logout-all/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data["sessions_invalidated"], 2)

        refresh_attempt = self.client.post("/api/accounts/login/refresh/", {"refresh": str(session2_refresh)})
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_all_requires_authentication(self):
        resp = self.client.post("/api/accounts/logout-all/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(**TEST_OVERRIDES)
class TwoFactorRecoveryCodeTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="recoveryuser", email="recoveryuser@example.com", password="RecoveryPass123!", role=User.Role.PATIENT
        )

    def _enable_2fa(self):
        self.client.force_authenticate(self.user)
        setup = self.client.post("/api/accounts/2fa/setup/")
        secret = setup.data["secret"]
        enable = self.client.post("/api/accounts/2fa/enable/", {"otp_code": pyotp.TOTP(secret).now()})
        self.client.force_authenticate(None)
        return enable.data["recovery_codes"]

    def test_enabling_2fa_returns_recovery_codes(self):
        codes = self._enable_2fa()
        self.assertEqual(len(codes), 8)
        self.assertEqual(len(set(codes)), 8)  # all unique

    def test_login_with_recovery_code_succeeds_without_otp(self):
        codes = self._enable_2fa()
        resp = self.client.post(
            "/api/accounts/login/", {"username": "recoveryuser", "password": "RecoveryPass123!", "recovery_code": codes[0]}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

    def test_recovery_code_is_single_use(self):
        codes = self._enable_2fa()
        first = self.client.post(
            "/api/accounts/login/", {"username": "recoveryuser", "password": "RecoveryPass123!", "recovery_code": codes[0]}
        )
        self.assertEqual(first.status_code, status.HTTP_200_OK)

        second = self.client.post(
            "/api/accounts/login/", {"username": "recoveryuser", "password": "RecoveryPass123!", "recovery_code": codes[0]}
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_recovery_code_rejected(self):
        self._enable_2fa()
        resp = self.client.post(
            "/api/accounts/login/",
            {"username": "recoveryuser", "password": "RecoveryPass123!", "recovery_code": "NOTREAL-CODE0000"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_regenerate_invalidates_old_codes(self):
        old_codes = self._enable_2fa()

        self.client.force_authenticate(self.user)
        regen = self.client.post("/api/accounts/2fa/recovery-codes/regenerate/")
        self.assertEqual(regen.status_code, status.HTTP_200_OK)
        new_codes = regen.data["recovery_codes"]
        self.client.force_authenticate(None)

        self.assertNotEqual(set(old_codes), set(new_codes))
        stale_attempt = self.client.post(
            "/api/accounts/login/", {"username": "recoveryuser", "password": "RecoveryPass123!", "recovery_code": old_codes[0]}
        )
        self.assertEqual(stale_attempt.status_code, status.HTTP_400_BAD_REQUEST)

        fresh_attempt = self.client.post(
            "/api/accounts/login/", {"username": "recoveryuser", "password": "RecoveryPass123!", "recovery_code": new_codes[0]}
        )
        self.assertEqual(fresh_attempt.status_code, status.HTTP_200_OK)

    def test_disabling_2fa_clears_recovery_codes(self):
        from .models import TwoFactorRecoveryCode

        self._enable_2fa()
        self.assertTrue(TwoFactorRecoveryCode.objects.filter(user=self.user).exists())

        self.client.force_authenticate(self.user)
        self.client.post("/api/accounts/2fa/disable/", {"password": "RecoveryPass123!"})
        self.assertFalse(TwoFactorRecoveryCode.objects.filter(user=self.user).exists())


@override_settings(**TEST_OVERRIDES)
class PasswordPolicyTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_short_password_rejected_on_registration(self):
        resp = self.client.post(
            "/api/accounts/register/",
            {"username": "shortpw", "email": "shortpw@example.com", "password": "Sh0rt!"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", resp.data)
