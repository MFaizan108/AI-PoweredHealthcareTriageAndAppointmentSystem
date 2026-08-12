from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import TwoFactorRecoveryCode, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "role", "first_name", "last_name", "is_staff", "is_active"]
    list_filter = ["role", "is_staff", "is_active"]
    fieldsets = UserAdmin.fieldsets + (
        ("Role info", {"fields": ("role", "phone_number")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role info", {"fields": ("role", "phone_number", "email")}),
    )


@admin.register(TwoFactorRecoveryCode)
class TwoFactorRecoveryCodeAdmin(admin.ModelAdmin):
    """Read-only visibility for support/incident response (e.g. bulk-delete a user's codes to force
    them to regenerate). The hash itself is never useful to display or edit."""

    list_display = ["user", "used_at", "created_at"]
    list_filter = ["used_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["user", "code_hash", "used_at", "created_at"]
