import json

from .models import AuditLog

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
LOGIN_PATH_SUFFIX = "/api/accounts/login/"


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


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
                status_code=response.status_code,
                ip_address=_client_ip(request),
                user_agent=user_agent,
            )
