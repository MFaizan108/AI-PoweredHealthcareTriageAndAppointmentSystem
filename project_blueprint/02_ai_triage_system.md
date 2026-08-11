# 2. AI Triage System — Project ka Hero Feature

Ye project ka sabse important part hai.

Patient enter kare:

> "I have fever, severe headache and difficulty breathing."

System symptoms ko process karega.

AI output:

```
Triage Assessment

Urgency: HIGH

Recommended Action:
Seek prompt medical evaluation.

Suggested Department:
Emergency / General Medicine

Symptoms Detected:
✓ Fever
✓ Headache
✓ Breathing difficulty

Reason:
Breathing difficulty can require urgent clinical assessment.

⚠ This is not a medical diagnosis.
```

## Triage Levels

### 🟢 Low
Routine appointment recommended.

### 🟠 Moderate
Doctor consultation recommended soon.

### 🔴 High
Prompt/urgent medical evaluation recommended.

### 🚨 Emergency
System should advise immediate emergency care rather than simply offering a routine appointment.

---
See diagram: [diagrams/ai_triage_layers.svg](diagrams/ai_triage_layers.svg)
