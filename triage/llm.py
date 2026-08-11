"""Layer 3 — LLM symptom summarizer, and a shared Ollama/Groq client other apps
(e.g. ai_assistant) reuse for their own prompts via ask_llm().

Purely a language-summarization aid. It never sets urgency or department —
those come exclusively from the Layer 1 rule engine. If the LLM is disabled,
unreachable, or errors out, triage still returns a complete result.
"""
import logging

import requests

from .models import AIProviderSettings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a clinical language assistant. Rewrite the patient's reported symptoms into one or two "
    "short, neutral clinical sentences (third person, e.g. 'The patient reports...'). "
    "Do NOT diagnose, do NOT suggest a specific disease, and do NOT recommend medication. "
    "Only summarize what was reported."
)


def _build_prompt(symptoms_text, detected_symptom_names, urgency):
    detected = ", ".join(detected_symptom_names) or "none confidently recognized"
    return (
        f"Patient-reported symptoms: {symptoms_text}\n"
        f"System-detected symptom keywords: {detected}\n"
        f"Rule-based urgency level (already determined, do not change it): {urgency}\n\n"
        "Write the clinical summary now."
    )


def _call_ollama(settings_obj, system_prompt, prompt):
    url = f"{settings_obj.ollama_base_url.rstrip('/')}/api/generate"
    payload = {
        "model": settings_obj.ollama_model,
        "prompt": f"{system_prompt}\n\n{prompt}",
        "stream": False,
    }
    response = requests.post(url, json=payload, timeout=settings_obj.timeout_seconds)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def _call_groq(settings_obj, system_prompt, prompt):
    if not settings_obj.groq_api_key:
        raise ValueError("Groq API key is not configured in AI Provider Settings.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings_obj.groq_api_key}"}
    payload = {
        "model": settings_obj.groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=settings_obj.timeout_seconds)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def ask_llm(system_prompt, user_prompt):
    """Generic Ollama/Groq call, shared by any app. Returns (text_or_None, provider, error_or_None)."""
    settings_obj = AIProviderSettings.get_solo()

    if not settings_obj.is_enabled:
        return None, None, "AI is disabled by admin."

    try:
        if settings_obj.provider == AIProviderSettings.Provider.GROQ:
            text = _call_groq(settings_obj, system_prompt, user_prompt)
        else:
            text = _call_ollama(settings_obj, system_prompt, user_prompt)
        return text, settings_obj.provider, None
    except Exception as exc:
        logger.warning("LLM call failed (%s): %s", settings_obj.provider, exc)
        return None, settings_obj.provider, str(exc)


def generate_ai_summary(symptoms_text, detected_symptom_names, urgency):
    """Returns (summary_text_or_None, provider_used_or_None, error_message_or_None)."""
    prompt = _build_prompt(symptoms_text, detected_symptom_names, urgency)
    return ask_llm(SYSTEM_PROMPT, prompt)
