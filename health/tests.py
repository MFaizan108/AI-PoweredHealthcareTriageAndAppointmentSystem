from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings


class HealthEndpointTests(TestCase):
    """No authentication anywhere here on purpose — these endpoints are for load balancers/uptime
    monitors, which can't hold a JWT. DB/cache checks hit the real backends configured for this
    test run (Postgres always; Redis if REDIS_CACHE_URL is set, else Django's LocMemCache
    fallback — either way check_cache() should report healthy)."""

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_aggregate_health_endpoint_reports_all_healthy(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            body,
            {"api": "healthy", "database": "healthy", "redis": "healthy", "celery": "healthy"},
        )

    def test_db_health_endpoint(self):
        response = self.client.get("/health/db/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["database"]["status"], "healthy")

    def test_redis_health_endpoint(self):
        response = self.client.get("/health/redis/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redis"]["status"], "healthy")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_celery_health_endpoint_in_eager_mode(self):
        response = self.client.get("/health/celery/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["celery"]["status"], "healthy")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_celery_health_endpoint_reports_unhealthy_when_no_worker_responds(self):
        with patch("ai_healthcare_triage_appointment_system.celery.app.control") as mock_control:
            mock_control.inspect.return_value.ping.return_value = None
            response = self.client.get("/health/celery/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["celery"]["status"], "unhealthy")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_celery_health_endpoint_reports_healthy_when_a_worker_responds(self):
        with patch("ai_healthcare_triage_appointment_system.celery.app.control") as mock_control:
            mock_control.inspect.return_value.ping.return_value = {"worker1@host": {"ok": "pong"}}
            response = self.client.get("/health/celery/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["celery"]["status"], "healthy")

    def test_database_health_endpoint_reports_unhealthy_on_connection_error(self):
        # The whole point of a health check is that it never itself 500s — whatever the DB driver
        # throws must turn into a clean "unhealthy" JSON response, not a crashed request.
        with patch("health.checks.connection") as mock_connection:
            mock_connection.cursor.side_effect = Exception("connection refused")
            response = self.client.get("/health/db/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["database"]["status"], "unhealthy")

    def test_health_endpoints_do_not_require_authentication(self):
        for url in ["/health/", "/health/db/", "/health/redis/", "/health/celery/"]:
            response = self.client.get(url)
            self.assertNotEqual(response.status_code, 401)
            self.assertNotEqual(response.status_code, 403)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_metrics_endpoint_is_public_and_exposes_request_counter(self):
        self.client.get("/health/")  # generate at least one sample
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"django_http_requests_total", response.content)
        self.assertIn(b"django_http_request_duration_seconds", response.content)
