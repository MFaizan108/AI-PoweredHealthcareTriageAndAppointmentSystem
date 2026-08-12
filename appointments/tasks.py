from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from notifications.models import Notification
from notifications.services import notify


@shared_task
def send_appointment_reminders():
    """Runs hourly via Celery Beat. Reminds patients about tomorrow's appointments, once each."""
    from .models import Appointment

    tomorrow = timezone.localdate() + timedelta(days=1)
    due = (
        Appointment.objects.filter(appointment_date=tomorrow, reminder_sent=False)
        .exclude(status=Appointment.Status.CANCELLED)
        .select_related("patient__user", "doctor__user")
    )

    sent = 0
    for appointment in due:
        notify(
            appointment.patient.user,
            Notification.NotificationType.APPOINTMENT_REMINDER,
            "Appointment Reminder",
            f"Reminder: you have an appointment with {appointment.doctor} tomorrow ({appointment.appointment_date}) at {appointment.slot_start_time}.",
        )
        appointment.reminder_sent = True
        appointment.save(update_fields=["reminder_sent"])
        sent += 1

    return sent
