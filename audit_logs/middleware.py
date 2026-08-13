import json
import re

from rest_framework.settings import api_settings

from .models import AuditLog

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
LOGIN_PATH_SUFFIX = "/api/accounts/login/"

OBJECT_ID_PATTERN = re.compile(r"/(\d+)/(?:[a-z0-9-]+/)?$")

# Never persist these into the audit trail, even redacted-in-place — the log itself must not become
# a secrets store. Matched case-insensitively against JSON body keys at any nesting depth.
REDACTED_KEYS = {
    "password",
    "new_password",
    "old_password",
    "current_password",
    "otp_code",
    "recovery_code",
    "token",
    "refresh",
    "access",
    "groq_api_key",
    "secret",
    "otp_secret",
}


def _client_ip(request):
    # Must mirror DRF's own SimpleRateThrottle.get_ident() exactly (same NUM_PROXIES setting) —
    # nginx's X-Forwarded-For is client-supplied-then-appended-to
    # ($proxy_add_x_forwarded_for), so trusting the *first* entry (as this used to) let any client
    # put an arbitrary fake IP in the audit trail — including their own login-history page (see
    # accounts.views.LoginHistoryView) — just by sending their own X-Forwarded-For header. Only the
    # last `num_proxies` hops were actually appended by infrastructure we control; everything
    # before that is untrusted, attacker-controlled input.
    num_proxies = api_settings.NUM_PROXIES
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if not forwarded or not num_proxies:
        return request.META.get("REMOTE_ADDR")
    addrs = [addr.strip() for addr in forwarded.split(",")]
    return addrs[-min(num_proxies, len(addrs))]


def _extract_object_id(path):
    match = OBJECT_ID_PATTERN.search(path)
    return match.group(1) if match else ""


def _redact(value):
    if isinstance(value, dict):
        return {key: ("***REDACTED***" if key.lower() in REDACTED_KEYS else _redact(val)) for key, val in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _redacted_body(request):
    try:
        body = json.loads(request.body or b"{}")
    except Exception:
        return {}
    if not isinstance(body, dict):
        return {}
    return _redact(body)


def _attempted_username(request):
    # Login requests may arrive as JSON, form-encoded, or multipart (browsable API, curl, various clients)
    # — request.POST only populates for form/multipart, so try JSON first and fall back to it.
    try:
        body = json.loads(request.body or b"{}")
        username = body.get("username", "")
        if username:
            return str(username)[:150]
    except Exception:
        pass
    return str(request.POST.get("username", ""))[:150]


class AuditLogMiddleware:
    """Logs mutating API requests and login attempts. Runs after the view executes,
    so request.user already reflects JWT authentication (DRF propagates it back)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        path = request.path
        if not path.startswith("/api/"):
            return response

        try:
            self._log(request, response, path)
        except Exception:
            pass  # audit logging must never break the actual request

        return response

    def _log(self, request, response, path):
        user = getattr(request, "user", None)
        user = user if (user and getattr(user, "is_authenticated", False)) else None

        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        if path.endswith(LOGIN_PATH_SUFFIX) and request.method == "POST":
            attempted_username = _attempted_username(request)
            action = AuditLog.Action.LOGIN_SUCCESS if response.status_code == 200 else AuditLog.Action.LOGIN_FAILED
            logged_in_user = None
            if action == AuditLog.Action.LOGIN_SUCCESS:
                from accounts.models import User

                logged_in_user = User.objects.filter(username=attempted_username).first()
            AuditLog.objects.create(
                user=logged_in_user,
                username_attempted=attempted_username,
                action=action,
                method=request.method,
                path=path,
                status_code=response.status_code,
                ip_address=_client_ip(request),
                user_agent=user_agent,
            )
            return

        if request.method in MUTATING_METHODS:
            AuditLog.objects.create(
                user=user,
                action=AuditLog.Action.REQUEST,
                method=request.method,
                path=path,
                object_id=_extract_object_id(path),
                changes=_redacted_body(request) if request.method != "DELETE" else {},
                status_code=response.status_code,
                ip_address=_client_ip(request),
                user_agent=user_agent,
            )
