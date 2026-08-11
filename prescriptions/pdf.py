from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def render_prescription_pdf(prescription):
    buffer = BytesIO()
    doc = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 25 * mm

    def line(text, size=11, gap=7 * mm, bold=False):
        nonlocal y
        doc.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        doc.drawString(20 * mm, y, text)
        y -= gap

    line("AI-Powered Healthcare Triage & Appointment System", 14, bold=True)
    line("Prescription", 12, bold=True, gap=10 * mm)

    line(f"Patient: {prescription.patient.user.get_full_name() or prescription.patient.user.username}")
    line(f"Doctor: {prescription.doctor}")
    line(f"Date: {prescription.created_at.strftime('%Y-%m-%d')}", gap=10 * mm)

    line("Medicines:", bold=True)
    for item in prescription.items.all():
        line(f"- {item.medicine_name}  {item.dosage}  {item.frequency}  {item.duration}", size=10)
        if item.instructions:
            line(f"    Instructions: {item.instructions}", size=9)

    if prescription.notes:
        y -= 5 * mm
        line("Notes:", bold=True)
        line(prescription.notes, size=10)

    y -= 10 * mm
    line("This prescription was issued electronically and does not require a signature.", size=8)

    doc.showPage()
    doc.save()
    buffer.seek(0)
    return buffer
