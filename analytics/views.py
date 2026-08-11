from django.db.models import Avg, Count, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin
from appointments.models import Appointment
from patients.models import Patient
from triage.models import TriageAssessment


class PatientAnalyticsSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    new_patients_this_month = serializers.IntegerField()
    returning_patients = serializers.IntegerField()
    gender_distribution = serializers.DictField()
    age_distribution = serializers.DictField()
    department_utilization = serializers.DictField()
    patients_per_month = serializers.ListField()


class AppointmentAnalyticsSerializer(serializers.Serializer):
    total_appointments = serializers.IntegerField()
    by_status = serializers.DictField()
    average_waiting_time_minutes = serializers.FloatField(allow_null=True)
    doctor_wise_appointments = serializers.ListField()
    appointments_per_month = serializers.ListField()


class AIAnalyticsSerializer(serializers.Serializer):
    total_assessments = serializers.IntegerField()
    by_urgency = serializers.DictField()
    emergency_escalations = serializers.IntegerField()
    clinician_reviewed_count = serializers.IntegerField()
    clinician_agreements = serializers.IntegerField()
    clinician_disagreements = serializers.IntegerField()
    ai_vs_clinician_agreement_rate_percent = serializers.FloatField(allow_null=True)
    note = serializers.CharField()


def _age_bucket(dob, today):
    if not dob:
        return "unknown"
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 18:
        return "0-17"
    if age < 30:
        return "18-29"
    if age < 45:
        return "30-44"
    if age < 60:
        return "45-59"
    return "60+"


@extend_schema(tags=["Analytics"], responses=PatientAnalyticsSerializer, description="Admin-only: patient demographics, growth, and department utilization.")
class PatientAnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        month_start = today.replace(day=1)

        total_patients = Patient.objects.count()
        new_this_month = Patient.objects.filter(user__date_joined__date__gte=month_start).count()
        returning = Patient.objects.filter(appointments__isnull=False).distinct().count()

        gender_distribution = dict(
            Patient.objects.values_list("gender").annotate(count=Count("id")).order_by()
        )

        department_utilization = dict(
            Appointment.objects.exclude(status=Appointment.Status.CANCELLED)
            .values_list("doctor__department__name")
            .annotate(count=Count("id"))
            .order_by()
        )

        age_distribution = {}
        for dob in Patient.objects.values_list("date_of_birth", flat=True):
            bucket = _age_bucket(dob, today)
            age_distribution[bucket] = age_distribution.get(bucket, 0) + 1

        patients_per_month = list(
            Patient.objects.annotate(month=TruncMonth("user__date_joined"))
            .values("month").annotate(count=Count("id")).order_by("month")
        )

        return Response({
            "total_patients": total_patients,
            "new_patients_this_month": new_this_month,
            "returning_patients": returning,
            "gender_distribution": gender_distribution,
            "age_distribution": age_distribution,
            "department_utilization": department_utilization,
            "patients_per_month": patients_per_month,
        })


@extend_schema(tags=["Analytics"], responses=AppointmentAnalyticsSerializer, description="Admin-only: appointment volume, status breakdown, waiting times, and per-doctor load.")
class AppointmentAnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Appointment.objects.all()
        by_status = dict(qs.values_list("status").annotate(count=Count("id")).order_by())

        avg_wait = qs.filter(
            checked_in_at__isnull=False, consultation_started_at__isnull=False
        ).annotate(
            wait_seconds=F("consultation_started_at") - F("checked_in_at")
        ).aggregate(avg=Avg("wait_seconds"))["avg"]

        avg_wait_minutes = round(avg_wait.total_seconds() / 60, 1) if avg_wait else None

        doctor_wise = list(
            qs.exclude(status=Appointment.Status.CANCELLED)
            .values("doctor_id", "doctor__user__first_name", "doctor__user__last_name")
            .annotate(count=Count("id")).order_by("-count")
        )

        appointments_per_month = list(
            qs.annotate(month=TruncMonth("appointment_date"))
            .values("month").annotate(count=Count("id")).order_by("month")
        )

        return Response({
            "total_appointments": qs.count(),
            "by_status": by_status,
            "average_waiting_time_minutes": avg_wait_minutes,
            "doctor_wise_appointments": doctor_wise,
            "appointments_per_month": appointments_per_month,
        })


@extend_schema(tags=["Analytics"], responses=AIAnalyticsSerializer, description="Admin-only: triage urgency distribution and AI-vs-clinician agreement rate (monitoring metric, not a clinical accuracy claim).")
class AIAnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = TriageAssessment.objects.all()
        by_urgency = dict(qs.values_list("urgency").annotate(count=Count("id")).order_by())

        reviewed = qs.filter(clinician_agrees__isnull=False)
        agreements = reviewed.filter(clinician_agrees=True).count()
        disagreements = reviewed.filter(clinician_agrees=False).count()
        reviewed_count = reviewed.count()
        agreement_rate = round(agreements / reviewed_count * 100, 1) if reviewed_count else None

        return Response({
            "total_assessments": qs.count(),
            "by_urgency": by_urgency,
            "emergency_escalations": qs.filter(urgency=TriageAssessment.Urgency.EMERGENCY).count(),
            "clinician_reviewed_count": reviewed_count,
            "clinician_agreements": agreements,
            "clinician_disagreements": disagreements,
            "ai_vs_clinician_agreement_rate_percent": agreement_rate,
            "note": "Monitoring metric only — not a claim of clinical accuracy without proper validation.",
        })
