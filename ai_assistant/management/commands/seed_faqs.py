from django.core.management.base import BaseCommand

from ai_assistant.models import HospitalFAQ


class Command(BaseCommand):
    help = "Seed a starter set of hospital FAQs for the AI patient assistant."

    def handle(self, *args, **options):
        faqs = [
            ("What are your visiting hours?", "General visiting hours are 10:00 AM to 8:00 PM daily. Emergency is open 24/7."),
            ("How do I book an appointment?", "You can book an appointment through the app by selecting a department, doctor, date, and an available time slot."),
            ("How do I cancel or reschedule my appointment?", "Open your appointment and use the cancel option, then book a new slot if you need to reschedule."),
            ("Where can I see my prescriptions?", "Your prescriptions are listed on your patient dashboard under Prescriptions, linked to each visit."),
            ("How do I get my lab report?", "Lab reports appear on your dashboard once the lab uploads them, and you'll get a notification."),
            ("What should I do in a medical emergency?", "Go to the nearest emergency room immediately or call emergency services. Do not wait for an appointment."),
            ("How do I contact the reception desk?", "Please visit the front desk in person or call the hospital's main line for reception assistance."),
        ]
        created = 0
        for question, answer in faqs:
            _, was_created = HospitalFAQ.objects.get_or_create(question=question, defaults={"answer": answer})
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"FAQs seeded: {len(faqs)} total, {created} newly created."))
