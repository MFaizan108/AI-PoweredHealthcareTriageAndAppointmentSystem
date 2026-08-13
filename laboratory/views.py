import os

from django.http import FileResponse, Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import User
from doctors.models import Doctor
from notifications.models import Notification
from notifications.services import notify

from .models import LabReport, LabTest
from .permissions import CanAccessLabReport, CanAccessLabTest, _check_lab_access
from .serializers import LabReportSerializer, LabTestSerializer


class LabTestViewSet(viewsets.ModelViewSet):
    queryset = LabTest.objects.select_related("patient__user", "requested_by__user").prefetch_related("report")
    serializer_class = LabTestSerializer
    permission_classes = [CanAccessLabTest]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser or user.role in (User.Role.ADMIN, User.Role.LAB_STAFF):
            pass  # unrestricted
        elif user.role == User.Role.PATIENT:
            qs = qs.filter(patient__user=user)
        elif user.role == User.Role.DOCTOR:
            qs = qs.filter(requested_by__user=user)
        else:
            return qs.none()
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
        if user.is_superuser or user.role in (User.Role.ADMIN, User.Role.LAB_STAFF):
            return qs
        if user.role == User.Role.PATIENT:
            return qs.filter(lab_test__patient__user=user)
        if user.role == User.Role.DOCTOR:
            return qs.filter(lab_test__requested_by__user=user)
        return qs.none()

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


@extend_schema(
    tags=["lab"],
    responses={200: OpenApiTypes.BINARY},
    description=(
        "Streams the report file itself, gated by the same access rule as the report resource "
        "(CanAccessLabReport) — the file is never reachable via a public/unauthenticated media URL."
    ),
)
class LabReportDownloadView(APIView):
    """The report resource's `report_file` field points here rather than a raw MEDIA_URL path —
    nginx's /media/ location has no concept of DRF permissions, so serving the file straight from
    there would make every uploaded lab report reachable by anyone who ever saw its URL, forever."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        report = LabReport.objects.select_related("lab_test__patient__user", "lab_test__requested_by__user").filter(pk=pk).first()
        if not report:
            raise Http404
        test = report.lab_test
        if not _check_lab_access(request.user, test.patient, test.requested_by, "GET"):
            raise PermissionDenied("You do not have access to this lab report.")
        if not report.report_file:
            raise Http404("No file has been uploaded for this report.")
        return FileResponse(report.report_file.open("rb"), as_attachment=True, filename=os.path.basename(report.report_file.name))
