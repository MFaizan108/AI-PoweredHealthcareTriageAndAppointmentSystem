import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_healthcare_triage_appointment_system.settings")

app = Celery("ai_healthcare_triage_appointment_system")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "send-appointment-reminders-hourly": {
        "task": "appointments.tasks.send_appointment_reminders",
        "schedule": crontab(minute=0),  # every hour, on the hour
    },
}
