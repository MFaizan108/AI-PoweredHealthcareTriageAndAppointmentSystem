# 17. Database

PostgreSQL.

Possible core models:

- User
- Role
- Patient
- Doctor
- Department
- DoctorAvailability
- Appointment
- TriageAssessment
- Symptom
- MedicalRecord
- Diagnosis
- Prescription
- PrescriptionItem
- LabTest
- LabReport
- Notification
- Message
- Invoice
- Payment
- AuditLog

Redis bhi add kar sakte ho:

```
Django
   │
   ├── PostgreSQL
   │
   ├── Redis
   │
   └── Celery
```

Celery:

- appointment reminders
- email notifications
- background AI processing
- report processing
