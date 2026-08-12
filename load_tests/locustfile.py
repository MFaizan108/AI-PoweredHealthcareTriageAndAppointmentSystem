"""
Load test for the three endpoints called out in Phase 7 of the roadmap:
    /api/appointments/   (booking)
    /api/triage/assess/  (rule-based + async AI triage)
    /api/ai-assistant/ask/ (RAG assistant)

Usage (from the `main/` directory, with the venv activated and the target server already running —
either `manage.py runserver` for a quick check, or a real gunicorn/nginx deployment for a meaningful
50/100/500/1000-user run):

    locust -f load_tests/locustfile.py --host http://127.0.0.1:8001

Then open http://127.0.0.1:8089 and set the number of users / spawn rate, or run headless:

    locust -f load_tests/locustfile.py --host http://127.0.0.1:8001 --headless -u 100 -r 10 -t 2m

Seeds its own reference data AND a pool of pre-authenticated patient accounts on start, so the file is
self-contained. Deliberately does NOT drive traffic through /api/accounts/register/ or /login/ during
the timed run — those are correctly rate-limited (5/minute) per source IP, and a real distinct-user
production population naturally spreads across many IPs, so hammering them from one load-test box
would only measure the rate limiter, not the app. Booking/triage/assistant are the endpoints this
file is meant to characterize.

Safe to point at a scratch/dev database only — creates real Appointment/TriageAssessment/
AssistantQueryLog rows for every simulated user.
"""

import os
import random

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_healthcare_triage_appointment_system.settings")
django.setup()

from locust import HttpUser, between, events, task  # noqa: E402

USER_POOL_SIZE = 50


def _seed_reference_data():
    """Idempotent: safe to call every time locust starts. Creates one department/doctor/availability
    so booking and triage have something real to work against, plus a pool of patient accounts with
    JWTs minted directly (bypassing the throttled HTTP register/login endpoints, on purpose)."""
    import datetime

    from rest_framework_simplejwt.tokens import RefreshToken

    from accounts.models import User
    from departments.models import Department
    from doctors.models import Doctor, DoctorAvailability
    from triage.models import Symptom

    dept, _ = Department.objects.get_or_create(name="Load Test Department")

    doctor_user, created = User.objects.get_or_create(
        username="loadtest_doctor",
        defaults={"email": "loadtest_doctor@example.com", "role": User.Role.DOCTOR},
    )
    if created:
        doctor_user.set_password("LoadTestPass123!")
        doctor_user.save()
    doctor = Doctor.objects.filter(user=doctor_user).first()
    if doctor.department_id != dept.id:
        doctor.department = dept
        doctor.save(update_fields=["department"])

    for weekday in range(7):
        DoctorAvailability.objects.get_or_create(
            doctor=doctor,
            weekday=weekday,
            defaults={"start_time": datetime.time(8, 0), "end_time": datetime.time(20, 0), "slot_duration_minutes": 10},
        )

    Symptom.objects.get_or_create(
        name="Load Test Fever",
        defaults={"keywords": "fever, high temperature", "severity_weight": 2, "suggested_department": dept},
    )

    tokens = []
    for i in range(USER_POOL_SIZE):
        username = f"loadtest_patient_{i}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": f"{username}@example.com", "role": User.Role.PATIENT},
        )
        if created:
            user.set_password("LoadTestPass123!")
            user.save()
        tokens.append(str(RefreshToken.for_user(user).access_token))

    return doctor.id, tokens


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    environment.doctor_id, environment.user_tokens = _seed_reference_data()


class PatientJourney(HttpUser):
    """Each simulated user picks a pre-provisioned account and repeatedly books, triages, and asks
    the assistant a question — a rough mix of the platform's three heaviest endpoints."""

    wait_time = between(1, 3)

    def on_start(self):
        token = random.choice(self.environment.user_tokens)
        self.headers = {"Authorization": f"Bearer {token}"}
        self.doctor_id = self.environment.doctor_id

    @task(3)
    def check_available_slots(self):
        date_str = _next_weekday_str()
        self.client.get(
            f"/api/appointments/available-slots/?doctor={self.doctor_id}&date={date_str}",
            headers=self.headers,
            name="/api/appointments/available-slots/",
        )

    @task(2)
    def book_appointment(self):
        date_str = _next_weekday_str()
        slots_resp = self.client.get(
            f"/api/appointments/available-slots/?doctor={self.doctor_id}&date={date_str}",
            headers=self.headers,
            name="/api/appointments/available-slots/",
        )
        if slots_resp.status_code != 200:
            return
        available = [s for s in slots_resp.json() if s["available"]]
        if not available:
            return
        slot = random.choice(available)
        self.client.post(
            "/api/appointments/",
            {
                "doctor": self.doctor_id,
                "appointment_date": date_str,
                "slot_start_time": slot["start_time"],
                "reason": "Load test visit",
            },
            headers=self.headers,
            name="/api/appointments/ [POST]",
        )

    @task(3)
    def run_triage(self):
        self.client.post(
            "/api/triage/assess/",
            {"symptoms_text": "I have a fever and feel tired.", "use_ai_summary": False},
            headers=self.headers,
            name="/api/triage/assess/",
        )

    @task(1)
    def ask_assistant(self):
        self.client.post(
            "/api/ai-assistant/ask/",
            {"message": "When is my next appointment?"},
            headers=self.headers,
            name="/api/ai-assistant/ask/",
        )


def _next_weekday_str():
    import datetime

    return (datetime.date.today() + datetime.timedelta(days=random.randint(1, 6))).isoformat()
