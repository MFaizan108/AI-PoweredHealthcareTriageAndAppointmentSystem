# AI-Powered Healthcare Triage & Appointment System — Project Blueprint

> Status: **Planning / Blueprint only — implementation not started.**
> This folder is a one-time reference document. Do not change the features described here without an explicit decision to do so.

## 🏥 Core Idea

Patient apni symptoms enter karega → AI preliminary triage/risk assessment karega → suitable department/doctor suggest karega → appointment book hogi → doctor dashboard par patient ki information aur AI assessment available hogi.

**Important:** AI ko diagnosis system nahi banana. Isay "preliminary triage / decision-support" tak limit karna better hai, with clear disclaimer that it doesn't replace a qualified healthcare professional.

Scope note: **Backend-only** implementation is planned for this system.

## 📚 Blueprint Parts (Index)

| # | File | Covers |
|---|------|--------|
| 1 | [01_dashboards.md](01_dashboards.md) | Patient, Doctor, Admin/Hospital, Receptionist, Lab Staff dashboards |
| 2 | [02_ai_triage_system.md](02_ai_triage_system.md) | AI Triage System (hero feature) + Triage Levels |
| 3 | [03_ai_implementation_layers.md](03_ai_implementation_layers.md) | 3-layer AI architecture (Rule-based, ML, LLM) |
| 4 | [04_doctor_recommendation_system.md](04_doctor_recommendation_system.md) | Department/specialty recommendation |
| 5 | [05_appointment_system.md](05_appointment_system.md) | Smart Appointment System |
| 6 | [06_doctor_availability_engine.md](06_doctor_availability_engine.md) | Doctor Availability Engine / slot generation |
| 7 | [07_electronic_medical_record.md](07_electronic_medical_record.md) | EMR structure |
| 8 | [08_prescription_management.md](08_prescription_management.md) | Prescription Management |
| 9 | [09_lab_management.md](09_lab_management.md) | Lab Management workflow |
| 10 | [10_notification_system.md](10_notification_system.md) | Notification System |
| 11 | [11_security.md](11_security.md) | Security requirements |
| 12 | [12_analytics_dashboard.md](12_analytics_dashboard.md) | Analytics Dashboard |
| 13 | [13_billing_system.md](13_billing_system.md) | Billing System |
| 14 | [14_doctor_patient_communication.md](14_doctor_patient_communication.md) | Doctor–Patient Communication |
| 15 | [15_ai_patient_assistant.md](15_ai_patient_assistant.md) | AI Patient Assistant (RAG-based) |
| 16 | [16_django_apps_structure.md](16_django_apps_structure.md) | Recommended Django apps |
| 17 | [17_database_models.md](17_database_models.md) | Database (PostgreSQL, Redis, Celery) + core models |
| 18 | [18_overall_architecture.md](18_overall_architecture.md) | Overall system architecture |
| 19 | [19_advanced_features.md](19_advanced_features.md) | Advanced / flagship features |
| 20 | [20_roadmap_phases.md](20_roadmap_phases.md) | MVP → Advanced → Flagship roadmap + Final Dashboard Count |
| 21 | [21_roadmap_phase5_to_20.md](21_roadmap_phase5_to_20.md) | Post-backend roadmap: Phase 5 (API Docs) → Phase 20 (CV/Portfolio Release) |

Diagrams (pictures) are saved in [diagrams/](diagrams/):
- `architecture_overview.svg`
- `dashboards_overview.svg`
- `ai_triage_layers.svg`
- `appointment_flow.svg`
- `doctor_availability_slots.svg`
- `lab_workflow.svg`

## ⚠️ Guardrail (applies to every part below)

The AI component is a **preliminary triage / decision-support tool**, not a diagnostic system. Every AI output must carry a disclaimer that it does not replace a qualified healthcare professional. Rules/validated clinical logic + clinician review remain authoritative over any ML/LLM output.
