# AI Evaluation Report

Generated: 2026-08-13T00:21:46

## Rule Engine Evaluation (Layer 1)

```
Case                                     Expected     Actual       Result
--------------------------------------------------------------------------------
Red Flag -> Emergency                    emergency    emergency    PASS
High Severity (no red flag) -> High      high         high         PASS
Multiple Moderate -> Moderate            moderate     moderate     PASS
Low Severity -> Low                      low          low          PASS
Unknown / unrecognized input -> Safe fallback (Low, no department) low          low          PASS

Accuracy: 5/5 (100%)
```

## LLM Evaluation (Layer 3)

```
Provider   Success    Failure    Timeout    Invalid    Avg ms     Min ms     Max ms
------------------------------------------------------------------------------------------
ollama     100%       0%         0%         0%         11072      10578      12018
  - [success] 10578ms
  - [success] 12018ms
  - [success] 10619ms
groq       0%         100%       0%         0%         0          0          1
  - [failure] 1ms (Groq API key is not configured in AI Provider Settings.)
  - [failure] 0ms (Groq API key is not configured in AI Provider Settings.)
  - [failure] 0ms (Groq API key is not configured in AI Provider Settings.)
```

## RAG Authorization Evaluation

```
Case                                     Expected   Actual           Result
--------------------------------------------------------------------------------
Patient A asks about Patient B           DENY       DENY             PASS
Patient A asks about own appointment     ALLOW      ALLOW            PASS

RAG must never bypass authorization: HOLDS
```

