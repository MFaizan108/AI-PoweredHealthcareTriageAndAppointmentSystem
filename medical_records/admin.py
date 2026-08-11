from django.contrib import admin

from .models import Diagnosis, MedicalRecord


class DiagnosisInline(admin.TabularInline):
    model = Diagnosis
    extra = 0


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ["patient", "doctor", "visit_date", "created_at"]
    list_filter = ["visit_date"]
    search_fields = ["patient__user__username", "doctor__user__username"]
    inlines = [DiagnosisInline]


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ["medical_record", "description", "diagnosed_at"]
