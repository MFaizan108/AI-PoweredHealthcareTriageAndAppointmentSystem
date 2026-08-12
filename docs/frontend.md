# Frontend

`frontend/` is a React 19 + TypeScript + Vite single-page app — a separate codebase from the
Django backend, talking to it purely over the existing JWT REST API (nothing in `frontend/`
imports or depends on Django directly).

**Status (Phase 11, complete):** auth (login incl. 2FA/recovery-code, register) + all five
role dashboards — Patient, Doctor, Receptionist, Lab Staff, Admin. Verified end-to-end in a real
headless-browser run chaining all five roles together against the live backend (Doctor sets
availability → Receptionist registers a walk-in patient and books them → Doctor treats them
(record, prescription, lab request) → Lab Staff processes and delivers the report → Admin creates
the staff accounts and reviews analytics/audit logs) — zero console/network errors on the final
run.

## Stack

- **React 19 + TypeScript + Vite** — plain SPA, not Next.js: everything here is auth-gated
  dashboards, so there's no SEO/SSR need.
- **react-router-dom** — client-side routing.
- **@tanstack/react-query** — server-state fetching/caching/polling (e.g. the triage AI-summary
  poll, the notification-bell unread count).
- **axios** — HTTP client, with a request interceptor that attaches the JWT and a response
  interceptor that transparently refreshes an expired access token (see below).
- **No component library** — hand-written CSS (`src/index.css`) using CSS custom properties for
  the design tokens (colors/radius/shadow), rather than pulling in MUI/Ant/etc. Kept the bundle
  small and avoided a second design system fighting the backend's own plain, functional style.

## Folder structure

```
frontend/src/
├── api/              one file per backend app (appointments.ts, triage.ts, ...), plus
│                      client.ts (axios instance + interceptors), types.ts (mirrors DRF
│                      serializers), tokenStorage.ts, auth.ts
├── auth/              AuthContext (current user, login/logout), ProtectedRoute (login guard),
│                      RoleGuard (per-role dashboard guard)
├── components/
│   ├── layout/         Sidebar, Topbar, NotificationBell, DashboardLayout
│   ├── ui/              Card, Badge, Spinner, ErrorBanner, EmptyState — small shared primitives
│   └── PatientPicker.tsx  search-as-you-type patient lookup, used by every staff role's
│                      "act on behalf of a patient" flows (book/record/prescribe/request-lab/invoice)
├── dashboards/         per-role nav item lists (patientNav.ts, doctorNav.ts, receptionistNav.ts,
│                      labStaffNav.ts, adminNav.ts)
├── pages/
│   ├── auth/            LoginPage, RegisterPage
│   ├── patient/          Patient dashboard sections
│   ├── doctor/           Doctor dashboard sections (incl. self-service Availability — see below)
│   ├── receptionist/     Receptionist dashboard sections
│   ├── labstaff/         Lab Staff dashboard sections
│   ├── admin/            Admin dashboard sections
│   ├── shared/           Pages reused by more than one role as-is:
│   │                       MessagesPage (patient/doctor, role-aware counterpart label),
│   │                       NotificationsPage (every role's topbar bell target),
│   │                       PatientsSearchPage (doctor/receptionist/admin patient lookup),
│   │                       StaffAppointmentsPage (receptionist/admin: book-for-patient + manage)
│   └── DashboardPendingPage.tsx   generic fallback if a role has no landing path
├── App.tsx             route tree (one guarded subtree per role)
├── roleRouting.ts       role -> landing path
└── format.ts            date/time/currency formatting helpers
```

## Auth flow

- Tokens live in `localStorage` (not an httpOnly cookie) — this matches the backend's existing
  bearer-token design (every endpoint expects `Authorization: Bearer <token>`, not a session
  cookie); the backend's CSP (`settings.py SECURE_CSP`) is the mitigation for the localStorage/XSS
  risk that comes with that, same as any other bearer-token API.
- On login, if the account has 2FA enabled, the backend's 400 response is detected
  (`auth.ts#is2FARequiredError`) and the login form reveals an authenticator-code field (or a
  "use a recovery code instead" toggle) rather than treating it as a bad-credentials error.
- `client.ts`'s response interceptor catches a `401`, calls
  `POST /api/accounts/login/refresh/` once (concurrent 401s share a single in-flight refresh
  promise, since the backend blacklists the old refresh token on rotation — a second concurrent
  refresh call would already be invalid), retries the original request, and on refresh failure
  broadcasts a `healthcare:session-expired` window event that `AuthContext` listens for to clear
  the logged-in state (kept as an event rather than a direct import to avoid a circular
  dependency between the axios layer and the React context).
- `RoleGuard` keeps one role's dashboard tree from being reachable by another logged-in role (e.g.
  a receptionist following a stale `/admin` bookmark) — bounces to that user's own landing page.

## Role dashboards

| Role | Sections |
|---|---|
| Patient | Overview, Appointments, AI Triage, Medical Records, Prescriptions, Lab Reports, Billing, Messages, Notifications |
| Doctor | Today's Queue, Appointments, Patients, Medical Records (create), Prescriptions (create), Lab Requests (create), **Availability**, Messages, My Activity |
| Receptionist | Queue (with check-in), Walk-in Registration, Patient Search, Appointments (book on behalf of a patient) |
| Lab Staff | Pending Tests, Processing (+ inline report upload), Reports |
| Admin | Overview, Users (incl. create staff accounts), Doctors (edit profiles), Patients, Departments, Appointments, Billing, AI Analytics, Audit Logs, System Settings (AI provider config) |

**Doctor Availability** wasn't in the original roadmap list for this dashboard, but was added
because it's a real functional gap, not scope creep: a brand-new doctor account has zero
`DoctorAvailability` rows, so `get_available_slots` returns nothing and nobody — patient,
receptionist, or admin — can ever book them through the UI. Self-service weekly-window management
(add/remove) closes that gap; the `doctors.ts` API for it already existed from the Patient-phase
build-out (`listAvailability`/`createAvailability`/`deleteAvailability`).

`getAvailableSlots()` (`api/appointments.ts`) also dedupes the response by `start_time` — the
backend doesn't dedupe across overlapping/duplicate `DoctorAvailability` windows for the same
weekday (`appointments/services.py`), so without this a doctor with two overlapping windows would
render duplicate slot buttons.

## Dev workflow

```
cd frontend
npm install
npm run dev        # Vite on :5173
```
`vite.config.ts` proxies `/api`, `/health`, `/media` to `http://127.0.0.1:8000` — run the Django
dev server (`python manage.py runserver`) alongside it. No `VITE_API_BASE_URL` or similar is
needed: every API call in this app uses a relative path (`/api/...`), which resolves correctly
under both the dev proxy and the production nginx proxy (see below) without a build-time switch.

**Windows/Git Bash note:** this repo's path contains an `&` — some `npm run <script>` invocations
go through a cmd.exe shim that mis-splits on it. If `npm run dev`/`build` fails with a
path/"command not found" error, invoke the tool directly instead:
`node ./node_modules/vite/bin/vite.js` / `node ./node_modules/typescript/bin/tsc -b`.

## Production build & serving

`frontend/Dockerfile` is a two-stage build: `node:22-alpine` runs `npm ci && npm run build`, then
the static `dist/` output is copied into an `nginx:1.27-alpine` stage. `docker-compose.yml`'s
`nginx` service (`--profile production`) builds from this Dockerfile — the same nginx container
that terminates TLS and reverse-proxies the API also serves the compiled React app, so there's one
cert setup and one place to look, not two. `nginx/templates/default.conf.template` routes
`/api/*`, `/admin/*`, `/health/*` to the Django `web` container and falls back everything else to
`try_files ... /index.html` (so client-side routes like `/patient/appointments` survive a hard
refresh) — see [deployment.md](deployment.md).
