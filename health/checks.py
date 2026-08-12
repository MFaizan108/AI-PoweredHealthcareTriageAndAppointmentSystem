from django.conf import settings
from django.core.cache import cache
from django.db import connection


def check_database():
    # Deliberately a broad `except Exception`, not just OperationalError: the entire point of a
    # health check is to never itself crash with a 500 — whatever the DB driver throws (connection
    # refused, auth failure, etc.) should turn into a clean "unhealthy" JSON response.
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True, "ok"
    except Exception as exc:  # noqa: BLE001 - intentionally broad, see above
        return False, str(exc)


def check_cache():
    """Round-trips a value through whatever CACHES['default'] backend is configured — Redis in
    production, Django's in-process LocMemCache in local dev/tests when REDIS_CACHE_URL is unset
    (mirrors the same conditional pattern used in settings.py)."""
    probe_key = "health_check_probe"
    try:
        cache.set(probe_key, "ok", timeout=5)
        if cache.get(probe_key) != "ok":
            return False, "cache round-trip returned an unexpected value"
        return True, "ok"
    except Exception as exc:  # noqa: BLE001 - backend-specific connection errors vary (redis.exceptions.*)
        return False, str(exc)


def check_celery():
    if settings.CELERY_TASK_ALWAYS_EAGER:
        # No broker/worker involved at all in this mode — tasks run synchronously in-process, so
        # there is nothing further to check.
        return True, "eager mode (CELERY_TASK_ALWAYS_EAGER=True) — no broker/worker required"

    from ai_healthcare_triage_appointment_system.celery import app as celery_app

    try:
        replies = celery_app.control.inspect(timeout=2).ping()
        if not replies:
            return False, "no Celery worker responded to ping"
        return True, f"{len(replies)} worker(s) responding"
    except Exception as exc:  # noqa: BLE001 - broker connection errors vary by backend
        return False, str(exc)
