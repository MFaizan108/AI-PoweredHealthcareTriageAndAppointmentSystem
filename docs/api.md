# API Reference

> This is a human-readable index. For the full, always-in-sync request/response schema — including every
> field, type, and example — use the generated docs while the server is running:
>
> - **Swagger UI** (interactive, try real requests): `/api/docs/`
> - **ReDoc** (read-only reference): `/api/redoc/`
> - **Raw OpenAPI 3 schema** (YAML): `/api/schema/`
>
> See [authentication.md](authentication.md) for login/2FA/token details and
> [permissions.md](permissions.md) for who can call what.

## Base URL

All endpoints are namespaced under `/api/`. There is no version segment yet — see
[architecture.md](architecture.md#api-versioning-strategy) for the versioning plan.

## Endpoint groups

| Prefix | App | Notes |
|---|---|---|
| `/api/accounts/` | accounts | Auth, 2FA, verification, password reset, user management — see [authentication.md](authentication.md) |
| `/api/departments/` | departments | CRUD, admin-write / authenticated-read |
| `/api/patients/` | patients | CRUD, self-or-staff scoped; `GET /me/` for the current patient's own profile |
| `/api/doctors/` | doctors | `DoctorViewSet`, `/availability/`, `/leaves/` |
| `/api/appointments/` | appointments | Booking + `/available-slots/`, `/queue/`, `/<id>/cancel/`, `/<id>/check-in/`, `/<id>/set-status/`, `/waitlist/`, `/feedback/` |
| `/api/medical-records/` | medical_records | EMR entries + nested diagnoses |
| `/api/prescriptions/` | prescriptions | CRUD + `/<id>/pdf/` |
| `/api/lab/` | laboratory | Lab test requests and reports |
| `/api/notifications/` | notifications | Read-only + `/mark-read/`, `/mark-all-read/` |
| `/api/triage/` | triage | `/assess/` (run triage), `/assessments/`, `/symptoms/`, `/emergency-guidance/`, `/ai-settings/` |
| `/api/ai-assistant/` | ai_assistant | `/ask/` (RAG Q&A), `/faqs/`, `/history/` |
| `/api/billing/` | billing | Invoices and payments |
| `/api/messages/` | messaging | Per-appointment patient↔doctor messages |
| `/api/analytics/` | analytics | Admin-only: `/patients/`, `/appointments/`, `/ai/` |
| `/api/audit-logs/` | audit_logs | Admin-only audit trail |

Exact sub-paths (action names, route ordering) are authoritative in Swagger UI / ReDoc, not here — this
table is for orientation.

## Pagination

List endpoints use DRF `PageNumberPagination` (`PAGE_SIZE = 20`):
```
GET /api/patients/?page=2
```
```json
{
  "count": 42,
  "next": "http://.../api/patients/?page=3",
  "previous": "http://.../api/patients/?page=1",
  "results": [ ... ]
}
```

## Filtering

There is no generic filter backend (`django-filter`) installed — filtering is implemented per-view via
explicit query params read in `get_queryset()`. The common ones:

| Param | Used on | Effect |
|---|---|---|
| `?role=` | `/api/accounts/users/` | Filter users by role |
| `?search=` | `/api/patients/` | Search across username/name/phone/email |
| `?department=` | `/api/doctors/` | Filter doctors by department |
| `?doctor=` | availability/leave/appointments/waitlist/feedback endpoints | Scope to one doctor |
| `?patient=` | medical-records, triage assessments | Scope to one patient (staff only — patients are already self-scoped) |
| `?status=` | `/api/appointments/` | Filter by appointment status |
| `?date=` | `/api/appointments/`, `/api/appointments/queue/` | Filter/scope to one date (`YYYY-MM-DD`) |
| `?unread=1` | `/api/notifications/` | Only unread notifications |

## Error responses

Standard DRF error shape. Validation errors are field-keyed; everything else is a `detail` string:

```json
// 400 — validation error
{ "slot_start_time": ["This field is required."] }

// 400 / 403 / 404 — everything else
{ "detail": "Not found." }
```

| Status | Meaning here |
|---|---|
| `400 Bad Request` | Validation failure, or a business-rule rejection (e.g. double-booking a slot, feedback on a non-completed appointment) |
| `401 Unauthorized` | Missing/invalid/expired JWT |
| `403 Forbidden` | Authenticated but not permitted for this action (role/ownership check failed) |
| `404 Not Found` | Object doesn't exist **or** exists but is filtered out of the requester's queryset (deliberate — see [permissions.md](permissions.md#object-level-vs-queryset-level-enforcement)) |
| `429 Too Many Requests` | Rate limit exceeded (`anon` 30/min, `user` 120/min, `login` 5/min) |
| `500 Internal Server Error` | Unexpected — should never happen; if the LLM is down, `triage/assess` and `ai-assistant/ask` degrade gracefully instead of erroring (see below) |

## AI endpoints degrade gracefully

`POST /api/triage/assess/` and `POST /api/ai-assistant/ask/` never fail with a 500 just because the
configured LLM (Ollama/Groq) is slow or unreachable:
- Triage: the rule-based urgency/department result is always returned; only `ai_summary` is empty and
  `ai_summary_error` is populated.
- Assistant: a friendly fallback message is returned in `response`, with `error` populated.

## Request/response examples

Full, per-endpoint request and response bodies (including all optional fields and enum values) are
generated directly from the serializers and kept in sync automatically — see Swagger UI (`/api/docs/`),
which also lets you authorize with a real JWT and execute requests against a running server.
