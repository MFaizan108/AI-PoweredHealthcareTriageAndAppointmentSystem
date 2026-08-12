from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import DoctorAvailability


@receiver([post_save, post_delete], sender=DoctorAvailability)
def invalidate_doctor_availability_cache(sender, instance, **kwargs):
    """Keeps the per-(doctor, weekday) cache in appointments/services.py correct whenever the
    schedule is edited — via the API or directly in the Django admin."""
    from django.core.cache import cache

    from appointments.services import doctor_availability_cache_key

    cache.delete(doctor_availability_cache_key(instance.doctor_id, instance.weekday))
