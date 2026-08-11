from datetime import datetime, timedelta

from doctors.models import DoctorAvailability, DoctorLeave

from .models import Appointment


def _time_to_dt(d, t):
    return datetime.combine(d, t)


def is_doctor_on_leave(doctor, date):
    return DoctorLeave.objects.filter(doctor=doctor, start_date__lte=date, end_date__gte=date).exists()


def get_available_slots(doctor, date):
    """Generate the day's slots for a doctor and mark which ones are already booked.

    Returns a list of dicts: {"start_time", "end_time", "available"}.
    """
    if is_doctor_on_leave(doctor, date):
        return []

    weekday = date.weekday()  # Monday=0 ... Sunday=6, matches DoctorAvailability.Weekday
    availabilities = DoctorAvailability.objects.filter(doctor=doctor, weekday=weekday, is_active=True)

    booked_start_times = set(
        Appointment.objects.filter(doctor=doctor, appointment_date=date)
        .exclude(status=Appointment.Status.CANCELLED)
        .values_list("slot_start_time", flat=True)
    )

    slots = []
    for availability in availabilities:
        cursor = _time_to_dt(date, availability.start_time)
        end = _time_to_dt(date, availability.end_time)
        step = timedelta(minutes=availability.slot_duration_minutes)

        while cursor + step <= end:
            slot_start = cursor.time()
            slot_end = (cursor + step).time()
            slots.append(
                {
                    "start_time": slot_start,
                    "end_time": slot_end,
                    "available": slot_start not in booked_start_times,
                }
            )
            cursor += step

    slots.sort(key=lambda s: s["start_time"])
    return slots


def generate_token_number(doctor, date):
    """Sequential per-doctor, per-day token, e.g. A-101, A-102 ..."""
    count = Appointment.objects.filter(doctor=doctor, appointment_date=date).exclude(
        status=Appointment.Status.CANCELLED
    ).count()
    return f"A-{100 + count + 1}"
