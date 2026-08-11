# 18. Overall Architecture

Final system kuch is tarah ho sakta hai:

```
                  ┌───────────────┐
                  │    Patient    │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │   Django API  │
                  └───────┬───────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
      AI Triage      Appointment        Medical
        Engine          Engine           Records
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                    PostgreSQL
                          │
                    ┌─────┴─────┐
                    ▼           ▼
                  Redis       Celery
```

---
See diagram: [diagrams/architecture_overview.svg](diagrams/architecture_overview.svg)
