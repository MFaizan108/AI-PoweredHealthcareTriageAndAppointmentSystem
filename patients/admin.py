from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["__str__", "gender", "blood_group", "date_of_birth"]
    search_fields = ["user__username", "user__first_name", "user__last_name"]
