from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Department


@receiver([post_save, post_delete], sender=Department)
def invalidate_department_list_cache(sender, instance, **kwargs):
    """Keeps the cached list in views.py correct whenever a department is edited — via the API
    or directly in the Django admin."""
    from django.core.cache import cache

    from .views import LIST_CACHE_KEY

    cache.delete(LIST_CACHE_KEY)
