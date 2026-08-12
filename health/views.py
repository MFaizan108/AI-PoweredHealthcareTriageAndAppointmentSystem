from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .checks import check_cache, check_celery, check_database


def _result(ok, detail):
    return {"status": "healthy" if ok else "unhealthy", "detail": detail}


@require_GET
@never_cache
def health(request):
    """Aggregate health check for load balancers / uptime monitors. Deliberately a plain Django
    view (not a DRF APIView) so it bypasses JWT auth and the anon rate throttle entirely — infra
    monitoring hits this frequently and unauthenticated by design."""
    db_ok, db_detail = check_database()
    cache_ok, cache_detail = check_cache()
    celery_ok, celery_detail = check_celery()
    all_ok = db_ok and cache_ok and celery_ok

    return JsonResponse(
        {
            "api": "healthy",
            "database": "healthy" if db_ok else "unhealthy",
            "redis": "healthy" if cache_ok else "unhealthy",
            "celery": "healthy" if celery_ok else "unhealthy",
        },
        status=200 if all_ok else 503,
    )


@require_GET
@never_cache
def health_db(request):
    ok, detail = check_database()
    return JsonResponse({"database": _result(ok, detail)}, status=200 if ok else 503)


@require_GET
@never_cache
def health_redis(request):
    ok, detail = check_cache()
    return JsonResponse({"redis": _result(ok, detail)}, status=200 if ok else 503)


@require_GET
@never_cache
def health_celery(request):
    ok, detail = check_celery()
    return JsonResponse({"celery": _result(ok, detail)}, status=200 if ok else 503)
