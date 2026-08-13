# Demo Script

Phase 18 of the roadmap. Two things live here, both produced from one real, driven run against
the actual app — not staged mockups:

- **[docs/demo-recording.webm](demo-recording.webm)** — a ~40-second screen recording of a
  headless browser actually clicking through all 10 scenes below, captured via Playwright's
  native video recording while driving `frontend/` against a live Django backend.
- **[docs/screenshots/](screenshots/)** — one still per scene, pulled from that same run (also
  linked from the [README](../README.md#screenshots)).

A rendered, narrated video (voiceover, cuts, on-screen captions) is presentation work outside
what this environment can produce — the shot list, exact steps, and narration text below are
written so that part is a straightforward recording session on top of material already proven to
work, not a redesign.

## How this was produced

`accounts.management.commands.seed_demo` seeds a full connected dataset (see
[demo.md](demo.md)), then a Playwright script (`chromium`, headless) logs in as each seeded
account in turn and drives the real UI — registers a fresh account, submits real symptoms to the
real rule engine, reads real seeded appointments/records/prescriptions/lab reports/invoices/
messages, and reads the real audit log. Zero console errors, zero network errors, across two full
runs. The one hiccup during the actual capture session (documented for transparency, not
hidden): the login rate limiter (5/minute, a real Phase 8 protection) correctly throttled the
first attempt at logging into 6 different accounts within about a minute — fixed by reordering
scenes to reuse a session across scenes wherever the same role could stay logged in, from 6
logins down to 4.

## Shot list

| # | Scene | Account | What it shows | Still |
|---|---|---|---|---|
| 1 | Registration + login | new account, then `patient_ali` | Patient self-registration, then signing in to a seeded account with real history | [01](screenshots/01-patient-login.png) |
| 2 | AI triage | `patient_ali` | Symptoms → rule-based `Emergency` urgency + department + red-flag reasoning → background LLM explanation → emergency guidance | [02](screenshots/02-ai-triage.png) |
| 3 | Appointment booking | `patient_ali` | Existing + bookable appointments against real doctor availability | [03](screenshots/03-appointments.png) |
| 4 | Doctor dashboard | `dr_bilal` | Today's queue and appointment list | [04](screenshots/04-doctor-dashboard.png) |
| 5 | Medical record + prescription | `dr_bilal` | A real visit note + diagnosis, and a multi-item prescription | [05](screenshots/05-medical-records.png) |
| 6 | Lab test → report | `dr_bilal` → `lab_hassan` | Doctor's lab request, then the lab side: pending queue and a completed report | [06](screenshots/06-lab-reports.png) |
| 7 | Billing | `demo_admin` | Invoices (paid + partially paid) with consultation/lab charge breakdown | [07](screenshots/07-billing.png) |
| 8 | Messaging | `patient_ali` | A real patient↔doctor thread tied to a shared appointment | [08](screenshots/08-messaging.png) |
| 9 | Admin analytics | `demo_admin` | Patient/appointment/AI-urgency aggregates — explicitly labeled "monitoring metric only" | [09](screenshots/09-admin-analytics.png) |
| 10 | Security / architecture | `demo_admin` | The audit trail (who/what/when/from-where/status) and AI provider settings (encrypted key, never shown in plaintext) | [10](screenshots/10-audit-logs.png) |

## Narration draft

Written to read naturally over the recording above, roughly matched to its pacing — trim/expand
once actually voicing it.

1. **"Patients register and sign in with a bearer-token JWT session — no separate admin approval
   step."** *(registration form → dashboard)*
2. **"The hero feature: a patient describes symptoms in plain text. A deterministic rule engine —
   not an LLM — decides the urgency and department. Here, chest pain and difficulty breathing are
   red-flag symptoms, so it escalates straight to Emergency, with the reasoning shown, not
   hidden. An LLM then rewrites that already-decided result into plain language — it never
   overrides the rule engine's call."** *(symptom entry → Emergency result → AI explanation
   fills in → emergency guidance box)*
3. **"From there, the patient books against a real doctor's real weekly availability — no
   double-booking, generated time slots, not a static calendar."** *(appointments list)*
4. **"Switching to the doctor's view — today's queue and appointment list, scoped to only this
   doctor's own patients."** *(doctor queue)*
5. **"The doctor's visit produces a medical record with a diagnosis, and a prescription with
   dosage/frequency/duration per medicine."** *(records → prescriptions)*
6. **"A lab test request flows to the lab side of the system — pending, then processed, then a
   report the ordering doctor and the patient can both see."** *(lab requests → pending → report)*
7. **"Billing ties a visit's consultation fee and lab charges into one invoice, with partial or
   full payment tracking."** *(billing page)*
8. **"Patients and doctors message directly, scoped to their shared appointment — not an open
   inbox."** *(messages thread)*
9. **"Admins get aggregate analytics — patient growth, department load, AI urgency distribution —
   explicitly labeled as a monitoring metric, not a clinical accuracy claim."** *(analytics)*
10. **"And underneath all of it: every mutating request is audit-logged with who, what, when, and
    from where, rate limiting on auth endpoints, 2FA, and secrets like the LLM provider's API key
    encrypted at rest — never shown back in plaintext."** *(audit log → settings)*

## Reproducing it

```bash
python manage.py seed_demo
python manage.py runserver
cd frontend && npm run dev   # separate terminal
```

Then either walk through the shot list above by hand, or drive it — the project doesn't ship a
committed Playwright test project for this (it was written ad hoc for this capture, per the `run`
skill's guidance for browser-driven apps), but the [frontend.md](frontend.md) testing section
describes the same headless-Chromium approach used for every dashboard's verification this
project already relies on.
