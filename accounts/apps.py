from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"

    def ready(self):
        # Wire the 2FA-aware login form into the Django admin site — see accounts/admin_forms.py
        # for why /admin/ needs its own enforcement of the same is_2fa_enabled check the API login
        # already has.
        from django.contrib import admin

        import accounts.signals  # noqa: F401

        from .admin_forms import TwoFactorAdminAuthenticationForm

        admin.site.login_form = TwoFactorAdminAuthenticationForm
