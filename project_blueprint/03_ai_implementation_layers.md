# 3. AI kaise implement kar sakte ho?

Project ke liye 3-layer architecture best rahegi:

## Layer 1 — Rule-Based Triage

Python/Django rules:

```
symptom
   ↓
severity
   ↓
risk factors
   ↓
urgency
```

Ye deterministic safety layer hogi.

## Layer 2 — ML/AI Classification

Model symptoms ko classify kare:

```
Symptoms
   ↓
Feature Extraction
   ↓
ML Model
   ↓
Risk Category
```

Possible models:

- Logistic Regression
- Random Forest
- XGBoost
- Neural Network

## Layer 3 — LLM

LLM patient ke symptoms ko understandable language mein summarize kare.

For example:

```
Patient reported:
fever + cough + chest discomfort

AI Summary:
The patient reports respiratory symptoms...
```

**Best architecture:** LLM ko final medical decision-maker na banao. Rules/validated clinical logic + clinician review ko authoritative rakho.

---
See diagram: [diagrams/ai_triage_layers.svg](diagrams/ai_triage_layers.svg)
