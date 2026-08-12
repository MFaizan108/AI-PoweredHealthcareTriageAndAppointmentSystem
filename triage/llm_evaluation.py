"""Layer 3 evaluation — live latency/reliability measurement for the LLM summarizer.

Unlike triage/evaluation.py (deterministic rule-engine pass/fail), an LLM's output isn't
something we can assert exact equality on. What we *can* measure, per the roadmap, is
operational health: response latency, failure rate, timeout rate, invalid-response rate,
and a side-by-side comparison of the two configured providers (Ollama vs Groq).

Runs against whichever provider(s) are actually reachable — if a provider is down or
unconfigured (e.g. no Groq API key), that's a legitimate result: it shows up as a 100%
failure rate rather than crashing the evaluation. No database writes.
"""
import copy
import time

from .llm import SYSTEM_PROMPT, _build_prompt, ask_llm
from .models import AIProviderSettings

# Representative prompts spanning the shapes triage actually sends to the LLM.
LLM_EVAL_SAMPLES = [
    {"symptoms_text": "I have a mild fever and a cough.", "detected_symptom_names": ["Fever", "Cough"], "urgency": "low"},
    {"symptoms_text": "Severe chest pain radiating to my left arm.", "detected_symptom_names": ["Chest Pain"], "urgency": "emergency"},
    {"symptoms_text": "I've had a headache and feel dizzy since this morning.", "detected_symptom_names": ["Headache", "Dizziness"], "urgency": "moderate"},
]


def _classify(text, error):
    if error:
        low = error.lower()
        if "timeout" in low or "timed out" in low:
            return "timeout"
        return "failure"
    if not text:
        return "invalid_response"
    return "success"


def _provider_settings(provider):
    """An unsaved snapshot of the real singleton with `.provider` overridden — probes a
    specific provider without touching the persisted admin config or its cache."""
    base = AIProviderSettings.get_solo()
    snapshot = copy.copy(base)
    snapshot.provider = provider
    return snapshot


def evaluate_provider(provider, samples=LLM_EVAL_SAMPLES):
    settings_obj = _provider_settings(provider)
    calls = []

    for sample in samples:
        prompt = _build_prompt(sample["symptoms_text"], sample["detected_symptom_names"], sample["urgency"])
        start = time.monotonic()
        text, _, error = ask_llm(SYSTEM_PROMPT, prompt, settings_obj=settings_obj)
        latency_ms = (time.monotonic() - start) * 1000
        calls.append({"prompt": sample["symptoms_text"], "latency_ms": latency_ms, "outcome": _classify(text, error), "error": error})

    total = len(calls)
    outcomes = {"success": 0, "failure": 0, "timeout": 0, "invalid_response": 0}
    for c in calls:
        outcomes[c["outcome"]] += 1
    latencies = [c["latency_ms"] for c in calls]

    return {
        "provider": provider,
        "calls": calls,
        "total": total,
        "success_rate": outcomes["success"] / total if total else 0.0,
        "failure_rate": outcomes["failure"] / total if total else 0.0,
        "timeout_rate": outcomes["timeout"] / total if total else 0.0,
        "invalid_response_rate": outcomes["invalid_response"] / total if total else 0.0,
        "avg_latency_ms": sum(latencies) / total if total else 0.0,
        "min_latency_ms": min(latencies) if latencies else 0.0,
        "max_latency_ms": max(latencies) if latencies else 0.0,
    }


def run_llm_evaluation():
    """Returns per-provider metrics for both Ollama and Groq, for a side-by-side comparison."""
    return {
        AIProviderSettings.Provider.OLLAMA: evaluate_provider(AIProviderSettings.Provider.OLLAMA),
        AIProviderSettings.Provider.GROQ: evaluate_provider(AIProviderSettings.Provider.GROQ),
    }
