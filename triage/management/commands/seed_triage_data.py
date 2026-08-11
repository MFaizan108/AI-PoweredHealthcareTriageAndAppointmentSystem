from django.core.management.base import BaseCommand

from departments.models import Department
from triage.models import EmergencyGuidance, Symptom, TriageAssessment


class Command(BaseCommand):
    help = "Seed departments and a starter symptom-to-department/urgency mapping for the AI triage engine."

    def handle(self, *args, **options):
        dept_names = [
            "General Medicine", "Emergency", "Cardiology", "Dermatology", "Dentistry",
            "Ophthalmology", "Orthopedics", "Neurology", "Pulmonology", "Mental Health",
            "Gastroenterology", "ENT", "Gynecology", "Pediatrics",
        ]
        departments = {}
        for name in dept_names:
            dept, _ = Department.objects.get_or_create(name=name)
            departments[name] = dept
        self.stdout.write(self.style.SUCCESS(f"Departments ready: {len(departments)}"))

        C = Symptom.Category
        symptoms = [
            # name, category, keywords, severity_weight, red_flag, department
            ("Fever", C.GENERAL, "fever, high temperature, chills", 2, False, "General Medicine"),
            ("Cough", C.RESPIRATORY, "cough, coughing", 2, False, "Pulmonology"),
            ("Difficulty Breathing", C.RESPIRATORY, "difficulty breathing, shortness of breath, breathless, can't breathe, cant breathe", 6, True, "Emergency"),
            ("Chest Pain", C.CARDIAC, "chest pain, chest tightness, chest discomfort", 5, True, "Emergency"),
            ("Severe Headache", C.NEUROLOGICAL, "severe headache, worst headache, splitting headache", 4, False, "Neurology"),
            ("Headache", C.NEUROLOGICAL, "headache, head pain", 1, False, "General Medicine"),
            ("Loss of Consciousness", C.NEUROLOGICAL, "loss of consciousness, fainted, unconscious, passed out", 6, True, "Emergency"),
            ("Slurred Speech / Facial Droop", C.NEUROLOGICAL, "slurred speech, facial droop, one side weakness, face drooping", 6, True, "Emergency"),
            ("Severe Bleeding", C.GENERAL, "severe bleeding, heavy bleeding, uncontrolled bleeding", 6, True, "Emergency"),
            ("Suicidal Thoughts", C.MENTAL_HEALTH, "suicidal, want to die, self harm, self-harm, kill myself", 6, True, "Mental Health"),
            ("Abdominal Pain", C.GASTROINTESTINAL, "abdominal pain, stomach pain, stomach ache, belly pain", 3, False, "Gastroenterology"),
            ("Severe Abdominal Pain", C.GASTROINTESTINAL, "severe abdominal pain, severe stomach pain, unbearable stomach pain", 5, False, "Gastroenterology"),
            ("Nausea/Vomiting", C.GASTROINTESTINAL, "nausea, vomiting, throwing up", 2, False, "Gastroenterology"),
            ("Diarrhea", C.GASTROINTESTINAL, "diarrhea, loose motions", 2, False, "Gastroenterology"),
            ("Skin Rash", C.DERMATOLOGICAL, "skin rash, rash, hives, itchy skin", 1, False, "Dermatology"),
            ("Tooth Pain", C.DENTAL, "tooth pain, toothache, dental pain", 2, False, "Dentistry"),
            ("Eye Problems", C.OPHTHALMOLOGICAL, "eye pain, blurred vision, red eye, vision problems", 2, False, "Ophthalmology"),
            ("Joint Pain", C.MUSCULOSKELETAL, "joint pain, knee pain, joint swelling", 2, False, "Orthopedics"),
            ("Back Pain", C.MUSCULOSKELETAL, "back pain, lower back pain", 2, False, "Orthopedics"),
            ("Fracture/Injury", C.MUSCULOSKELETAL, "fracture, broken bone, severe injury, deformed limb", 5, False, "Orthopedics"),
            ("Sore Throat", C.ENT, "sore throat, throat pain", 1, False, "ENT"),
            ("Ear Pain", C.ENT, "ear pain, earache", 1, False, "ENT"),
            ("Anxiety/Low Mood", C.MENTAL_HEALTH, "anxiety, depressed, low mood, panic attack", 2, False, "Mental Health"),
            ("Fatigue", C.GENERAL, "fatigue, tiredness, weakness, low energy", 1, False, "General Medicine"),
            ("Dizziness", C.NEUROLOGICAL, "dizziness, dizzy, lightheaded", 2, False, "General Medicine"),
        ]

        created = 0
        for name, category, keywords, weight, red_flag, dept_name in symptoms:
            _, was_created = Symptom.objects.update_or_create(
                name=name,
                defaults={
                    "category": category,
                    "keywords": keywords,
                    "severity_weight": weight,
                    "red_flag": red_flag,
                    "suggested_department": departments[dept_name],
                },
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(f"Symptoms seeded: {len(symptoms)} total, {created} newly created."))

        guidance = [
            (
                TriageAssessment.Urgency.EMERGENCY, "This is a medical emergency",
                "Do not wait for an appointment. Go to the nearest emergency room immediately or call an ambulance. "
                "If you are with someone experiencing this, stay with them and keep them calm while help arrives.",
                "Pakistan: 1122 (Rescue), 15 (Police), 115 (Ambulance - varies by city)",
            ),
            (
                TriageAssessment.Urgency.HIGH, "Prompt medical evaluation needed",
                "Please seek medical care as soon as possible today — visit an emergency department or an urgent-care "
                "clinic if you cannot get a same-day appointment. Do not delay if symptoms worsen.",
                "Pakistan: 1122 (Rescue), 15 (Police)",
            ),
        ]
        for urgency, title, content, numbers in guidance:
            EmergencyGuidance.objects.update_or_create(
                urgency=urgency, defaults={"title": title, "content": content, "emergency_numbers": numbers}
            )
        self.stdout.write(self.style.SUCCESS(f"Emergency guidance seeded: {len(guidance)} entries."))
