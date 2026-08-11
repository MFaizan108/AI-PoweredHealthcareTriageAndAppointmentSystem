from django.contrib import admin

from .models import LabReport, LabTest


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ["test_name", "patient", "requested_by", "status", "requested_at"]
    list_filter = ["status"]
    search_fields = ["test_name", "patient__user__username"]


@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ["lab_test", "uploaded_by", "uploaded_at", "reviewed_by_doctor"]
