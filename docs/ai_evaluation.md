# AI Evaluation

Phase 11 proved the AI features work end-to-end in the UI. This phase evaluates them — the
rule engine's accuracy against a named scenario matrix, the LLM's operational reliability, and
— most importantly — that the RAG assistant can never leak one patient's data through another
patient's question.

## Running it

```
python manage.py evaluate_ai
python manage.py evaluate_ai --output docs/ai_evaluation_report.md
```

The command is safe to run against any environment, including a live/demo database:

- **Rule engine section** only upserts the canonical `seed_triage_data` symptom set (same
  idempotent fixture the demo seeding uses) — never touches custom admin edits destructively.
- **LLM section** makes stateless network calls only — no database writes at all.
- **RAG section** creates its fixture data (two patients, two appointments) inside a database
  transaction that is *always* rolled back, win or lose — nothing it creates is ever left behind.

A checked-in example run is at [ai_evaluation_report.md](ai_evaluation_report.md).

## Rule Engine Evaluation (Layer 1)

`triage/evaluation.py` runs a fixed, named matrix through `run_rule_based_triage()` and checks
the urgency it returns against the roadmap's five required categories:

| Case | Input shape | Expected |
|---|---|---|
| Red Flag → Emergency | A red-flag symptom present (e.g. chest pain) | `emergency` |
| High Severity → High | Non-red-flag symptoms summing ≥ 8 | `high` |
| Multiple Moderate → Moderate | Non-red-flag symptoms summing 4–7 | `moderate` |
| Low Severity → Low | A single mild symptom | `low` |
| Unknown → Safe fallback | Text matching no known symptom keywords | `low`, no department |

This is deterministic — the rule engine has no LLM dependency — so the evaluation asserts exact
equality and reports an accuracy percentage, not a subjective score.

## LLM Evaluation (Layer 3)

The LLM only ever rewrites the rule engine's already-decided result into plain language — it
can't change urgency or department — so what matters operationally is whether it's *available*
and *fast*, not graded correctness. `triage/llm_evaluation.py` sends a fixed set of sample
prompts through `ask_llm()` for each provider and classifies every call as:

- **success** — a non-empty response, no error
- **invalid_response** — no error, but an empty/blank response
- **timeout** — the underlying request timed out
- **failure** — anything else (connection refused, bad API key, HTTP error, ...)

...then reports success/failure/timeout/invalid-response rates plus avg/min/max latency,
**per provider**, so Ollama and Groq can be compared side by side. `ask_llm()` gained an optional
`settings_obj` parameter for this — the evaluator builds an unsaved snapshot of the real
`AIProviderSettings` singleton with just `.provider` overridden, so probing "what if this were
Groq" never reads stale cached config or writes to the admin's live settings.

If a provider is down or unconfigured, that's not a bug in the harness — it's a correct result
(100% failure rate), and the report says so plainly.

## RAG Evaluation — authorization matrix

This is the one the roadmap calls out as most important, and it's evaluated as a full-stack
check, not a unit test of an internal function in isolation:

```
Patient A asks about Patient B  ->  DENY
Patient A asks about own data   ->  ALLOW
```

`ai_assistant/rag_evaluation.py` creates two patients with distinct appointments, then drives
the real `POST /api/ai-assistant/ask/` endpoint as Patient A:

- **DENY case** — Patient A's message explicitly references Patient B's appointment token.
  The check passes only if that token is **absent** from the `AssistantQueryLog.retrieved_context`
  that was actually sent to the LLM — i.e. the retriever never even fetched Patient B's data,
  regardless of what the free-text question asked for.
- **ALLOW case** — Patient A asks about their own upcoming appointment. The check passes only if
  their own token **is present** in the retrieved context.

The authorization boundary is structural, not prompt-based: `AssistantAskView` resolves
`patient = get_object_or_404(Patient, user=request.user)` from the authenticated session and
`get_patient_context(patient)` only ever queries that one patient's related objects — there is
no code path where the LLM or the free-text question can widen whose data gets retrieved.

### A real bug this caught

The first live run of `evaluate_ai` (outside `manage.py test`) failed both RAG cases — not an
authorization bug, but Django's `ALLOWED_HOSTS` check rejecting DRF's `APIClient`, whose default
`SERVER_NAME` is `"testserver"`. Under `manage.py test`, Django's test-environment setup adds
`"testserver"` to `ALLOWED_HOSTS` automatically; a plain `manage.py` process never does. Fixed by
wrapping the RAG section's HTTP calls in `override_settings(ALLOWED_HOSTS=[...,  "testserver"])`
for the duration of the evaluation only. Worth calling out because it's exactly the kind of gap
that only shows up when a tool is actually run for real, not just under the test runner.

## Test coverage

`triage/tests_evaluation.py` and `ai_assistant/tests_evaluation.py` cover the evaluation harness
itself (not just the AI features it evaluates): the rule-engine matrix scores 100% against the
seeded data, each LLM outcome classification (success/failure/timeout/invalid_response) is
exercised with a mocked `requests.post`, the RAG matrix passes both cases, and — importantly —
a dedicated test confirms the RAG sandbox leaves zero rows behind (`User.objects.filter(username__startswith="rageval_")`
is empty after every run, transaction rollback included).
