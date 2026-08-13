from rest_framework.throttling import ScopedRateThrottle


class AIRateThrottle(ScopedRateThrottle):
    """Shared by every endpoint that triggers a real LLM call (triage's AI summary, the RAG
    assistant) — see the "ai" rate in DEFAULT_THROTTLE_RATES for why this needs to be stricter
    than the generic per-user rate."""

    scope = "ai"
