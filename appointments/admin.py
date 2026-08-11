from django.contrib import admin

from .models import Appointment, Feedback, Waitlist


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "token_number", "patient", "doctor", "appointment_date", "slot_start_time",
        "status", "checked_in",
    ]
    list_filter = ["status", "checked_in", "appointment_date"]
    search_fields = ["patient__user__username", "doctor__user__username", "token_number"]


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ["patient", "doctor", "preferred_date", "status", "created_at"]
    list_filter = ["status"]


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["patient", "doctor", "rating", "created_at"]
    list_filter = ["rating"]
