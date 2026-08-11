# Roles & Permissions

## Roles

Every user has exactly one `role` (`accounts.User.Role`), plus an independent `is_superuser` flag that
bypasses role checks everywhere (used for the Django admin/bootstrap account):

| Role | Value | Typical dashboard |
|---|---|---|
| Admin | `admin` | Hospital/system administration |
| Doctor | `doctor` | Consultations, records, prescriptions |
| Patient | `patient` | Booking, own records, AI assistant |
| Receptionist | `receptionist` | Walk-ins, check-in, queue |
| Lab Staff | `lab_staff` | Lab test processing |

`Doctor`/`Patient` profile rows are auto-created via a signal whenever a `User` with that role is created —
every doctor/patient user always has a corresponding `Doctor`/`Patient` row to hang permissions off of.

## Global defaults

- `DEFAULT_AUTHENTICATION_CLASSES`: JWT (primary) + Session auth (for the browsable API / admin).
- `DEFAULT_PERMISSION_CLASSES`: `IsAuthenticated` — every endpoint requires login unless explicitly
  overridden with `AllowAny` (registration, login, password-reset request/confirm, email-verify confirm).
- `DEFAULT_THROTTLE_RATES`: anon `30/minute`, authenticated `120/minute`, login `5/minute`.

## Permission pattern: "self or staff"

Most apps follow the same shape, implemented as a per-app `BasePermission` subclass:

1. **Staff roles** (admin, and often doctor/receptionist depending on the resource) get broad access,
   usually scoped further by `get_queryset()` (e.g. a doctor only ever sees their own patients'
   appointments, not the whole hospital's).
2. **Patients** are restricted to their own data — object-level checks compare
   `obj.patient.user_id == request.user.id` (or the same filter applied at the queryset level so a
   patient can never even see another patient's row, not just get a 403 on `retrieve`).
3. **`is_superuser`** always passes, for the bootstrap admin account.

| App | Permission class | Rule |
|---|---|---|
| accounts | `IsRole` (+ `IsAdmin`/`IsDoctor`/`IsPatient`/`IsReceptionist`/`IsLabStaff`), `IsAdminOrReceptionist` | Exact-role gate for admin-only or admin/receptionist-only endpoints |
| departments | `IsAdminOrReadOnly` | Anyone authenticated can read; only admin can write |
| patients | `IsSelfOrStaff` | Patient sees/edits only their own profile; staff roles see all, with search |
| doctors | `IsAdminOrOwnerDoctorOrReadOnly` | Anyone reads; only admin or the doctor themself can write their own profile/availability/leave |
| appointments | `CanManageAppointment` | Patient: own appointments only. Doctor: own appointments only. Admin/receptionist: unrestricted. Booking on someone else's behalf requires staff role |
| medical_records | `IsOwnerPatientOrTreatingDoctorOrAdmin` (+ `...ViaMedicalRecord` for nested `Diagnosis`) | Patient reads own records; only the treating doctor (or admin) can write |
| prescriptions | `IsOwnerPatientOrPrescribingDoctorOrAdmin` | Same pattern, scoped to the prescribing doctor |
| laboratory | `CanAccessLabTest`, `CanAccessLabReport` | Patient: own tests/reports. Doctor: tests they ordered. Lab staff: process/upload. Admin: all |
| triage | `CanAccessTriageAssessment`, `IsAdminOnly`, `IsAdminOrReadOnlyForAuthenticated` | Patient: own assessments only. Doctor: assessments tied to their appointments. `AIProviderSettings` (LLM provider/API key) is admin-only |
| billing | `CanAccessInvoice`, `CanAccessPayment` | Patient: own invoices/payments. Admin/receptionist: all |
| messaging | `IsConversationParticipant` | Only the two parties on the linked appointment (patient and doctor) can read/send |
| analytics | `IsAdmin` | Admin-only, no patient/doctor access at all |
| ai_assistant | `IsAdminOrReadOnlyForAuthenticated` (FAQs), inline check in `AssistantAskView` | Only a patient (or superuser) may call `/ask/`, and only ever against their own retrieved context — see below |
| audit_logs | admin-only read | Security/audit trail is never exposed to non-admins |

## Object-level vs. queryset-level enforcement

Wherever practical, restrictions are applied at the **queryset** level (`get_queryset()` filters out rows
the user isn't allowed to see) rather than only at the object level (`has_object_permission` on
`retrieve`/`update`). This matters for list endpoints and for `404` vs `403` behavior — a patient
requesting `GET /api/appointments/<other patient's id>/` gets a clean `404` (queryset-filtered out),
not a `403` that would confirm the object exists.

## AI assistant: authorization is never bypassed by the LLM

The `/api/ai-assistant/ask/` RAG pipeline is explicitly designed so the retrieval step — not the LLM — is
the authorization boundary:

```
User -> permission check (must be the patient asking about themself)
     -> retriever (queries scoped to *this* patient's own appointments/prescriptions/lab tests + public FAQs)
     -> LLM (only ever sees the already-scoped context, never raw DB access)
     -> response
```

The LLM cannot query the database and cannot be prompted into fetching another patient's data — the
retriever simply never puts it in the context it hands to the model. See Phase 12 of
[../project_blueprint/21_roadmap_phase5_to_20.md](../project_blueprint/21_roadmap_phase5_to_20.md) for the
planned automated test matrix that pins this behavior down (`Patient A asks about Patient B -> DENY`).

## Audit trail

`audit_logs.middleware.AuditLogMiddleware` logs every mutating request (`POST`/`PUT`/`PATCH`/`DELETE`) and
every login attempt, capturing: who (user, or `null` for anonymous/failed logins), what (method + path),
when (timestamp), from where (IP + user agent), which object (when derivable), and outcome. Only admins can
read the audit log via `/api/audit-logs/`.
