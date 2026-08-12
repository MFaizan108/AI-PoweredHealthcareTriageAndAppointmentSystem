"""Hand-rolled Prometheus instrumentation (via the `prometheus_client` library directly) rather
than the `django-prometheus` package: as of this writing django-prometheus 2.5.0 pins
`Django<6.1`, which would silently downgrade this project off Django 6.1 (and its built-in CSP
middleware, which several Phase 8 security fixes depend on) the moment it's installed. This gives
the same two metrics the roadmap actually needs (request latency -> API response time, request
count by status -> error rate) without that constraint.
"""
import time

from django.http import HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "django_http_requests_total",
    "Total HTTP requests processed",
    ["method", "view", "status"],
)

REQUEST_LATENCY = Histogram(
    "django_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "view"],
)


def _view_label(request):
    match = getattr(request, "resolver_match", None)
    if match is None:
        return "unresolved"
    # url_name (e.g. "appointment-list") rather than the raw path, so /api/patients/42/ and
    # /api/patients/7/ collapse into one low-cardinality label instead of one series per ID.
    return match.view_name or match.url_name or "unknown"


class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration = time.monotonic() - start
        view = _view_label(request)
        REQUEST_LATENCY.labels(method=request.method, view=view).observe(duration)
        REQUEST_COUNT.labels(method=request.method, view=view, status=response.status_code).inc()
        return response


def metrics_view(request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
