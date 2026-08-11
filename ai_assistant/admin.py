from django.contrib import admin

from .models import AssistantQueryLog, HospitalFAQ


@admin.register(HospitalFAQ)
class HospitalFAQAdmin(admin.ModelAdmin):
    list_display = ["question", "is_active"]
    search_fields = ["question", "answer"]


@admin.register(AssistantQueryLog)
class AssistantQueryLogAdmin(admin.ModelAdmin):
    list_display = ["user", "message", "provider_used", "created_at"]
    readonly_fields = [f.name for f in AssistantQueryLog._meta.fields]
    search_fields = ["user__username", "message"]
