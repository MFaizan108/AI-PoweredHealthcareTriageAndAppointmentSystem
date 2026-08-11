from django.contrib import admin

from .models import Doctor, DoctorAvailability, DoctorLeave


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ["__str__", "department", "specialization", "experience_years", "is_active"]
    list_filter = ["department", "is_active"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "specialization"]


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ["doctor", "weekday", "start_time", "end_time", "slot_duration_minutes", "is_active"]
    list_filter = ["weekday", "is_active"]


@admin.register(DoctorLeave)
class DoctorLeaveAdmin(admin.ModelAdmin):
    list_display = ["doctor", "start_date", "end_date", "reason"]
