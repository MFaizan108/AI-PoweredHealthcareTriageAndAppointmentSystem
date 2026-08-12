# Demo Environment

One command turns an empty database into a fully explorable system — every role has an account,
every doctor is actually bookable, and there's a clinical workflow's worth of history to look at
immediately, no manual clicking-through-the-UI setup required first.

```
docker compose up
python manage.py migrate
python manage.py seed_demo
```

Or locally, against `main/.venv`:

```
python manage.py migrate
python manage.py seed_demo
```

## What it creates

| Role | Username | Notes |
|---|---|---|
| Admin | `demo_admin` | `is_staff`/`is_superuser`, so the Django admin site (`/admin/`) is also usable |
| Doctor | `dr_ayesha` | Cardiology |
| Doctor | `dr_bilal` | General Medicine |
| Doctor | `dr_sara` | Dermatology |
| Receptionist | `reception_uzma` | |
| Lab Staff | `lab_hassan` | |
| Patient | `patient_ali` | |
| Patient | `patient_mariam` | |
| Patient | `patient_zain` | |

**Password for every account: `Demo@12345`.**

Plus, wired together into one coherent story rather than nine disconnected accounts:

- **Departments, symptoms, and hospital FAQs** — reuses the existing `seed_triage_data` /
  `seed_faqs` commands (idempotent upserts) as a first step.
- **Doctor availability** — every demo doctor gets a Monday–Friday 09:00–17:00 schedule
  (20-minute slots). Without this a doctor has zero bookable slots — a real gap discovered and
  documented during [Phase 11](frontend.md#role-dashboards); the demo seed doesn't repeat it.
- **Appointments** — two completed (in the past) and two upcoming (pending/confirmed), spanning
  three of the demo patients and doctors.
- **Medical records + diagnoses**, **prescriptions** (with medicine items), **lab tests** (one
  completed with an uploaded-style report, one still `requested` so the Lab Staff dashboard has
  something in its Pending Tests queue), **invoices + payments** (one fully paid, one partially
  paid), **messages** (a patient/doctor exchange on a shared appointment), and **notifications**
  — attached to the appointments/records above rather than seeded as disconnected rows.
- **AI examples** — two `TriageAssessment` rows run through the real Layer-1 rule engine (one
  low-urgency fever/cough case, one emergency-flagged chest-pain case — see
  [ai_evaluation.md](ai_evaluation.md) for how that engine itself is evaluated), plus one
  `AssistantQueryLog` row showing what a RAG assistant answer looks like. These carry a canned
  `ai_summary` string rather than a live LLM call, so seeding never depends on Ollama/Groq being
  reachable.

## Idempotency

Safe to re-run. Identity data (users, departments, doctor schedules) is get-or-created and never
duplicates. Password hashing goes through `User.objects.create_user()`, not a plain
`get_or_create()` — the latter would silently store the password in plaintext, since Django's
generic manager `.create()` doesn't hash anything.

The clinical data (appointments and everything hung off them — records, prescriptions, lab
tests, invoices) is anchored to *today's* date each run: "past" appointments are `N` days before
today, "upcoming" ones are `N` days after. Re-running the command on a later date is still safe —
it won't duplicate the appointments from the previous run (they're looked up by
doctor+date+start-time, which no longer matches "today"), but it will add a fresh set anchored to
the new "today". That's intentional: a demo environment should always have an actually-upcoming
appointment to look at, not one that's silently drifted into the past.

## Test coverage

`accounts/tests_seed_demo.py` covers: every role account exists with a correctly hashed, usable
password (verified by actually logging in via `/api/accounts/login/`, not just checking the hash);
every demo doctor has bookable availability; the full clinical workflow's row counts per demo
patient; and that running the command twice in the same test doesn't create a second copy of
anything.
