from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "action", "user", "username_attempted", "method", "path", "status_code", "ip_address"]
    list_filter = ["action", "method"]
    search_fields = ["user__username", "username_attempted", "path"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
