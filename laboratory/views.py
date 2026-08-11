from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from accounts.models import User
from doctors.models import Doctor
from notifications.models import Notification
from notifications.services import notify

from .models import LabReport, LabTest
from .permissions import CanAccessLabReport, CanAccessLabTest
from .serializers import LabReportSerializer, LabTestSerializer


class LabTestViewSet(viewsets.ModelViewSet):
    queryset = LabTest.objects.select_related("patient__user", "requested_by__user").prefetch_related("report")
    serializer_class = LabTestSerializer
    permission_classes = [CanAccessLabTest]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.PATIENT:
            qs = qs.filter(patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(requested_by__user=user)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.DOCTOR:
            doctor = Doctor.objects.filter(user=user).first()
            if not doctor:
                raise ValidationError("No doctor profile found for this user.")
            serializer.save(requested_by=doctor)
        else:
            serializer.save()


class LabReportViewSet(viewsets.ModelViewSet):
    queryset = LabReport.objects.select_related("lab_test__patient__user", "lab_test__requested_by__user")
    serializer_class = LabReportSerializer
    permission_classes = [CanAccessLabReport]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.PATIENT:
            qs = qs.filter(lab_test__patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(lab_test__requested_by__user=user)
        return qs

    def perform_create(self, serializer):
        report = serializer.save(uploaded_by=self.request.user)
        lab_test = report.lab_test
        lab_test.status = LabTest.Status.COMPLETED
        lab_test.save(update_fields=["status", "updated_at"])

        notify(
            lab_test.patient.user,
            Notification.NotificationType.LAB_REPORT_AVAILABLE,
            "Lab Report Available",
            f"Your report for '{lab_test.test_name}' is now available.",
        )
        if lab_test.requested_by:
            notify(
                lab_test.requested_by.user,
                Notification.NotificationType.LAB_REPORT_AVAILABLE,
                "Lab Report Ready for Review",
                f"Lab report for '{lab_test.test_name}' ({lab_test.patient}) is ready for your review.",
            )
