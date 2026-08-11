from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def create_role_profile(sender, instance, created, **kwargs):
    """Auto-create the matching profile stub whenever a patient/doctor user is created."""
    if not created:
        return

    if instance.role == User.Role.PATIENT:
        from patients.models import Patient

        Patient.objects.get_or_create(user=instance)
    elif instance.role == User.Role.DOCTOR:
        from doctors.models import Doctor

        Doctor.objects.get_or_create(user=instance)
