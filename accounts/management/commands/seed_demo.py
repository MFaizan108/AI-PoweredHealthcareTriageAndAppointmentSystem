"""One command, a fully explorable demo environment:

    python manage.py migrate
    python manage.py seed_demo

Creates one account per role, departments, doctor availability (so doctors are actually
bookable — see docs/frontend.md's note on why that matters), a clinical workflow's worth of
appointments/records/prescriptions/lab tests/invoices/messages/notifications, and a couple of
AI examples (a rule-based triage assessment + an assistant query log).

Idempotent at the identity level — users, departments, and doctor schedules are get-or-created
and safe to re-run. The date-anchored clinical data (appointments and what hangs off them) is
seeded relative to "today" each run, so re-running on a later date adds a fresh, currently-
upcoming appointment rather than leaving behind one that's now in the past — see docs/demo.md.
"""
import datetime

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User

DEMO_PASSWORD = "Demo@12345"


def get_or_create_user(username, **fields):
    user = User.objects.filter(username=username).first()
    if user:
        return user, False
    # .create_user() (not .objects.create()/get_or_create()) is required here — it's what
    # actually hashes the password; a plain get_or_create() would store it in plaintext.
    user = User.objects.create_user(username=username, password=DEMO_PASSWORD, **fields)
    return user, True


class Command(BaseCommand):
    help = "Seed a complete, idempotent demo environment: one account per role, departments, appointments, records, prescriptions, lab tests, invoices, messages, notifications, and AI examples."

    def handle(self, *args, **options):
        from departments.models import Department

        self.stdout.write("Seeding reference data (departments, symptoms, FAQs)...")
        call_command("seed_triage_data", verbosity=0)
        call_command("seed_faqs", verbosity=0)
        departments = {d.name: d for d in Department.objects.all()}

        admin = self._seed_admin()
        doctors = self._seed_doctors(departments)
        receptionist = self._seed_receptionist()
        lab_staff = self._seed_lab_staff()
        patients = self._seed_patients()

        appointments = self._seed_appointments(patients, doctors)
        self._seed_medical_records(appointments)
        self._seed_prescriptions(appointments)
        lab_tests = self._seed_lab_tests(patients, doctors, appointments)
        self._seed_invoices(appointments, lab_tests)
        self._seed_messages(appointments)
        self._seed_notifications(patients, appointments)
        self._seed_ai_examples(patients)

        self._print_summary(admin, doctors, receptionist, lab_staff, patients)

    # -- Identity -----------------------------------------------------------------

    def _seed_admin(self):
        user, created = get_or_create_user(
            "demo_admin", email="demo_admin@example.com", role=User.Role.ADMIN,
            first_name="Imran", last_name="Sheikh", is_staff=True, is_superuser=True, email_verified=True,
        )
        self.stdout.write(f"Admin: {user.username} ({'created' if created else 'already existed'})")
        return user

    def _seed_doctors(self, departments):
        from doctors.models import Doctor, DoctorAvailability

        specs = [
            dict(username="dr_ayesha", first_name="Ayesha", last_name="Khan", department="Cardiology",
                 specialization="Cardiologist", qualification="MBBS, FCPS (Cardiology)",
                 license_number="PMC-10234", experience_years=12, consultation_fee=2500),
            dict(username="dr_bilal", first_name="Bilal", last_name="Ahmed", department="General Medicine",
                 specialization="General Physician", qualification="MBBS, FCPS (Medicine)",
                 license_number="PMC-10456", experience_years=8, consultation_fee=1500),
            dict(username="dr_sara", first_name="Sara", last_name="Malik", department="Dermatology",
                 specialization="Dermatologist", qualification="MBBS, MD (Dermatology)",
                 license_number="PMC-10789", experience_years=6, consultation_fee=2000),
        ]

        doctors = {}
        for spec in specs:
            username = spec.pop("username")
            dept_name = spec.pop("department")
            user, created = get_or_create_user(
                username, email=f"{username}@example.com", role=User.Role.DOCTOR,
                first_name=spec["first_name"], last_name=spec["last_name"], email_verified=True,
            )
            doctor = Doctor.objects.get(user=user)
            doctor.department = departments[dept_name]
            doctor.specialization = spec["specialization"]
            doctor.qualification = spec["qualification"]
            doctor.license_number = spec["license_number"]
            doctor.experience_years = spec["experience_years"]
            doctor.consultation_fee = spec["consultation_fee"]
            doctor.save()

            for weekday in range(5):  # Monday-Friday
                DoctorAvailability.objects.get_or_create(
                    doctor=doctor, weekday=weekday, start_time=datetime.time(9, 0), end_time=datetime.time(17, 0),
                    defaults={"slot_duration_minutes": 20},
                )
            doctors[username] = doctor
            self.stdout.write(f"Doctor: {user.username} ({'created' if created else 'already existed'})")
        return doctors

    def _seed_receptionist(self):
        user, created = get_or_create_user(
            "reception_uzma", email="reception_uzma@example.com", role=User.Role.RECEPTIONIST,
            first_name="Uzma", last_name="Farooq", email_verified=True,
        )
        self.stdout.write(f"Receptionist: {user.username} ({'created' if created else 'already existed'})")
        return user

    def _seed_lab_staff(self):
        user, created = get_or_create_user(
            "lab_hassan", email="lab_hassan@example.com", role=User.Role.LAB_STAFF,
            first_name="Hassan", last_name="Raza", email_verified=True,
        )
        self.stdout.write(f"Lab Staff: {user.username} ({'created' if created else 'already existed'})")
        return user

    def _seed_patients(self):
        from patients.models import Patient

        specs = [
            dict(username="patient_ali", first_name="Ali", last_name="Raza", dob=datetime.date(1990, 5, 14),
                 gender="male", blood_group="O+", address="House 12, Street 5, Gulberg, Lahore",
                 emergency_contact_name="Fatima Raza", emergency_contact_phone="03001234567", allergies="Penicillin"),
            dict(username="patient_mariam", first_name="Mariam", last_name="Siddiqui", dob=datetime.date(1985, 11, 2),
                 gender="female", blood_group="A+", address="Flat 4B, DHA Phase 6, Karachi",
                 emergency_contact_name="Usman Siddiqui", emergency_contact_phone="03211234567", allergies=""),
            dict(username="patient_zain", first_name="Zain", last_name="Iqbal", dob=datetime.date(2001, 2, 20),
                 gender="male", blood_group="B+", address="Model Town, Islamabad",
                 emergency_contact_name="Noor Iqbal", emergency_contact_phone="03331234567", allergies="Dust, Pollen"),
        ]

        patients = {}
        for spec in specs:
            username = spec["username"]
            user, created = get_or_create_user(
                username, email=f"{username}@example.com", role=User.Role.PATIENT,
                first_name=spec["first_name"], last_name=spec["last_name"], email_verified=True,
            )
            patient = Patient.objects.get(user=user)
            patient.date_of_birth = spec["dob"]
            patient.gender = spec["gender"]
            patient.blood_group = spec["blood_group"]
            patient.address = spec["address"]
            patient.emergency_contact_name = spec["emergency_contact_name"]
            patient.emergency_contact_phone = spec["emergency_contact_phone"]
            patient.known_allergies = spec["allergies"]
            patient.save()
            patients[username] = patient
            self.stdout.write(f"Patient: {user.username} ({'created' if created else 'already existed'})")
        return patients

    # -- Clinical workflow ----------------------------------------------------------

    def _seed_appointments(self, patients, doctors):
        from appointments.models import Appointment

        today = datetime.date.today()
        specs = [
            dict(key="ali_bilal_past", patient="patient_ali", doctor="dr_bilal", date=today - datetime.timedelta(days=7),
                 start=datetime.time(9, 0), status=Appointment.Status.COMPLETED, reason="Fever and cough for 3 days.", token="A-101"),
            dict(key="mariam_ayesha_past", patient="patient_mariam", doctor="dr_ayesha", date=today - datetime.timedelta(days=3),
                 start=datetime.time(9, 20), status=Appointment.Status.COMPLETED, reason="Follow-up for hypertension.", token="A-101"),
            dict(key="zain_sara_upcoming", patient="patient_zain", doctor="dr_sara", date=today + datetime.timedelta(days=1),
                 start=datetime.time(10, 0), status=Appointment.Status.PENDING, reason="Persistent skin rash.", token="A-103"),
            dict(key="ali_ayesha_upcoming", patient="patient_ali", doctor="dr_ayesha", date=today + datetime.timedelta(days=5),
                 start=datetime.time(11, 0), status=Appointment.Status.CONFIRMED, reason="Chest discomfort on exertion.", token="A-102"),
        ]

        appointments = {}
        for spec in specs:
            doctor = doctors[spec["doctor"]]
            end_time = (datetime.datetime.combine(spec["date"], spec["start"]) + datetime.timedelta(minutes=20)).time()
            is_completed = spec["status"] == Appointment.Status.COMPLETED
            checked_in_at = timezone.make_aware(datetime.datetime.combine(spec["date"], spec["start"])) if is_completed else None
            appointment, created = Appointment.objects.get_or_create(
                doctor=doctor, appointment_date=spec["date"], slot_start_time=spec["start"],
                defaults=dict(
                    patient=patients[spec["patient"]], slot_end_time=end_time, status=spec["status"],
                    reason=spec["reason"], token_number=spec["token"],
                    checked_in=spec["status"] != Appointment.Status.PENDING,
                    checked_in_at=checked_in_at,
                    consultation_started_at=checked_in_at,
                    consultation_completed_at=checked_in_at + datetime.timedelta(minutes=20) if is_completed else None,
                ),
            )
            appointments[spec["key"]] = appointment
        self.stdout.write(f"Appointments: {len(appointments)} ready.")
        return appointments

    def _seed_medical_records(self, appointments):
        from medical_records.models import Diagnosis, MedicalRecord

        specs = [
            dict(key="ali_bilal_past", notes="Patient presented with fever (101F) and productive cough for 3 days. "
                 "Chest clear on auscultation. Advised rest, fluids, and paracetamol.",
                 diagnosis="Acute viral upper respiratory tract infection."),
            dict(key="mariam_ayesha_past", notes="Routine hypertension follow-up. BP 138/88, stable on current medication. "
                 "Advised to continue low-salt diet and monitor BP weekly.",
                 diagnosis="Essential hypertension, controlled."),
        ]
        count = 0
        for spec in specs:
            appointment = appointments[spec["key"]]
            record, created = MedicalRecord.objects.get_or_create(
                appointment=appointment,
                defaults=dict(
                    patient=appointment.patient, doctor=appointment.doctor,
                    visit_date=appointment.appointment_date, consultation_notes=spec["notes"],
                ),
            )
            Diagnosis.objects.get_or_create(medical_record=record, description=spec["diagnosis"])
            count += int(created)
        self.stdout.write(f"Medical records: {len(specs)} ready ({count} newly created).")

    def _seed_prescriptions(self, appointments):
        from prescriptions.models import Prescription, PrescriptionItem

        specs = [
            dict(key="ali_bilal_past", notes="Take with food. Return if fever persists beyond 5 days.", items=[
                dict(medicine_name="Paracetamol", dosage="500mg", frequency="Every 6 hours", duration="5 days", instructions="After meals"),
                dict(medicine_name="Cetirizine", dosage="10mg", frequency="Once daily", duration="5 days", instructions="At night"),
            ]),
            dict(key="mariam_ayesha_past", notes="Continue existing antihypertensive regimen.", items=[
                dict(medicine_name="Amlodipine", dosage="5mg", frequency="Once daily", duration="30 days", instructions="Morning, with water"),
            ]),
        ]
        created_count = 0
        for spec in specs:
            appointment = appointments[spec["key"]]
            prescription = Prescription.objects.filter(appointment=appointment).first()
            if prescription:
                continue
            prescription = Prescription.objects.create(
                patient=appointment.patient, doctor=appointment.doctor, appointment=appointment, notes=spec["notes"],
            )
            for item in spec["items"]:
                PrescriptionItem.objects.create(prescription=prescription, **item)
            created_count += 1
        self.stdout.write(f"Prescriptions: {len(specs)} ready ({created_count} newly created).")

    def _seed_lab_tests(self, patients, doctors, appointments):
        from laboratory.models import LabReport, LabTest

        lab_tests = {}

        completed_spec = dict(
            patient="patient_ali", doctor="dr_bilal", appointment="ali_bilal_past",
            test_name="Complete Blood Count", notes="Rule out bacterial infection.",
            result_summary="WBC 11,200/uL (mildly elevated), Hemoglobin 13.8 g/dL, Platelets normal. "
            "Findings consistent with a viral illness; no evidence of bacterial infection.",
        )
        test, created = LabTest.objects.get_or_create(
            patient=patients[completed_spec["patient"]], test_name=completed_spec["test_name"],
            requested_by=doctors[completed_spec["doctor"]],
            defaults=dict(
                appointment=appointments[completed_spec["appointment"]], notes=completed_spec["notes"],
                status=LabTest.Status.COMPLETED,
            ),
        )
        LabReport.objects.get_or_create(lab_test=test, defaults=dict(
            result_summary=completed_spec["result_summary"], reviewed_by_doctor=True,
            reviewed_at=test.requested_at,
        ))
        lab_tests["ali_cbc"] = test

        pending_spec = dict(
            patient="patient_mariam", doctor="dr_ayesha", appointment="mariam_ayesha_past",
            test_name="Lipid Profile", notes="Baseline cardiovascular risk assessment.",
        )
        test, _ = LabTest.objects.get_or_create(
            patient=patients[pending_spec["patient"]], test_name=pending_spec["test_name"],
            requested_by=doctors[pending_spec["doctor"]],
            defaults=dict(appointment=appointments[pending_spec["appointment"]], notes=pending_spec["notes"], status=LabTest.Status.REQUESTED),
        )
        lab_tests["mariam_lipid"] = test

        self.stdout.write(f"Lab tests: {len(lab_tests)} ready.")
        return lab_tests

    def _seed_invoices(self, appointments, lab_tests):
        from billing.models import Invoice, Payment

        specs = [
            dict(key="ali_bilal_past", appointment="ali_bilal_past", lab_test="ali_cbc", lab_charges=1200,
                 status=Invoice.Status.PAID, description="Consultation - Dr. Bilal Ahmed + Complete Blood Count"),
            dict(key="mariam_ayesha_past", appointment="mariam_ayesha_past", lab_test=None, lab_charges=0,
                 status=Invoice.Status.PARTIALLY_PAID, description="Consultation - Dr. Ayesha Khan"),
        ]
        created_count = 0
        for spec in specs:
            appointment = appointments[spec["appointment"]]
            invoice = Invoice.objects.filter(appointment=appointment).first()
            if invoice:
                continue
            invoice = Invoice.objects.create(
                patient=appointment.patient, appointment=appointment,
                lab_test=lab_tests.get(spec["lab_test"]) if spec["lab_test"] else None,
                description=spec["description"], consultation_fee=appointment.doctor.consultation_fee,
                lab_charges=spec["lab_charges"], status=spec["status"],
            )
            if spec["status"] == Invoice.Status.PAID:
                Payment.objects.create(invoice=invoice, amount=invoice.total_amount, method=Payment.Method.CASH)
            elif spec["status"] == Invoice.Status.PARTIALLY_PAID:
                Payment.objects.create(invoice=invoice, amount=invoice.total_amount / 2, method=Payment.Method.CARD)
            created_count += 1
        self.stdout.write(f"Invoices: {len(specs)} ready ({created_count} newly created).")

    def _seed_messages(self, appointments):
        from messaging.models import Message

        appointment = appointments["ali_bilal_past"]
        exchange = [
            (appointment.patient.user, appointment.doctor.user, "Hello Dr. Ahmed, should I continue the cough syrup after the fever is gone?"),
            (appointment.doctor.user, appointment.patient.user, "Yes, please finish the 5-day course even if you feel better sooner."),
        ]
        created_count = 0
        for sender, recipient, body in exchange:
            _, created = Message.objects.get_or_create(appointment=appointment, sender=sender, recipient=recipient, body=body)
            created_count += int(created)
        self.stdout.write(f"Messages: {len(exchange)} ready ({created_count} newly created).")

    def _seed_notifications(self, patients, appointments):
        from notifications.models import Notification

        specs = [
            dict(patient="patient_zain", type=Notification.NotificationType.APPOINTMENT_BOOKED,
                 title="Appointment booked", message="Your appointment with Dr. Sara Malik is confirmed for tomorrow at 10:00 AM."),
            dict(patient="patient_ali", type=Notification.NotificationType.LAB_REPORT_AVAILABLE,
                 title="Lab report available", message="Your Complete Blood Count report is now available on your dashboard."),
            dict(patient="patient_ali", type=Notification.NotificationType.PRESCRIPTION_AVAILABLE,
                 title="Prescription available", message="Dr. Bilal Ahmed has added a new prescription to your record."),
        ]
        created_count = 0
        for spec in specs:
            _, created = Notification.objects.get_or_create(
                recipient=patients[spec["patient"]].user, notification_type=spec["type"], title=spec["title"],
                defaults={"message": spec["message"]},
            )
            created_count += int(created)
        self.stdout.write(f"Notifications: {len(specs)} ready ({created_count} newly created).")

    def _seed_ai_examples(self, patients):
        from ai_assistant.models import AssistantQueryLog
        from triage.models import TriageAssessment
        from triage.rules_engine import run_rule_based_triage

        triage_specs = [
            dict(patient="patient_ali", symptoms_text="I have a mild fever and a cough since yesterday.",
                 ai_summary="The patient reports a mild fever and cough that started yesterday."),
            dict(patient="patient_zain", symptoms_text="Severe chest pain and shortness of breath since this morning.",
                 ai_summary="The patient reports severe chest pain with shortness of breath, onset this morning."),
        ]
        created_count = 0
        for spec in triage_specs:
            patient = patients[spec["patient"]]
            if TriageAssessment.objects.filter(patient=patient, symptoms_text=spec["symptoms_text"]).exists():
                continue
            matched, urgency, department, reasoning = run_rule_based_triage(spec["symptoms_text"])
            assessment = TriageAssessment.objects.create(
                patient=patient, symptoms_text=spec["symptoms_text"], urgency=urgency, suggested_department=department,
                reasoning=reasoning, ai_summary=spec["ai_summary"], ai_provider_used="ollama",
                ai_summary_status=TriageAssessment.AISummaryStatus.READY,
            )
            assessment.detected_symptoms.set(matched)
            created_count += 1
        self.stdout.write(f"Triage examples: {len(triage_specs)} ready ({created_count} newly created).")

        assistant_spec = dict(
            patient="patient_ali", message="When is my next appointment?",
            response="Your next appointment is with Dr. Ayesha Khan (Cardiology). Check your Appointments tab for the exact date and time.",
        )
        patient = patients[assistant_spec["patient"]]
        _, created = AssistantQueryLog.objects.get_or_create(
            user=patient.user, message=assistant_spec["message"],
            defaults={"response": assistant_spec["response"], "provider_used": "ollama"},
        )
        self.stdout.write(f"Assistant query example: ready ({'newly created' if created else 'already existed'}).")

    def _print_summary(self, admin, doctors, receptionist, lab_staff, patients):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo environment ready. Accounts (password for all: " + DEMO_PASSWORD + "):"))
        self.stdout.write(f"{'Role':<14} {'Username':<16} Name")
        self.stdout.write("-" * 50)
        self.stdout.write(f"{'Admin':<14} {admin.username:<16} {admin.get_full_name()}")
        for doctor in doctors.values():
            self.stdout.write(f"{'Doctor':<14} {doctor.user.username:<16} {doctor.user.get_full_name()} ({doctor.specialization})")
        self.stdout.write(f"{'Receptionist':<14} {receptionist.username:<16} {receptionist.get_full_name()}")
        self.stdout.write(f"{'Lab Staff':<14} {lab_staff.username:<16} {lab_staff.get_full_name()}")
        for patient in patients.values():
            self.stdout.write(f"{'Patient':<14} {patient.user.username:<16} {patient.user.get_full_name()}")
