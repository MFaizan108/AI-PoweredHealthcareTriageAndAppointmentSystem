from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LabReportDownloadView, LabReportViewSet, LabTestViewSet

router = DefaultRouter()
router.register("reports", LabReportViewSet, basename="lab-report")
router.register("", LabTestViewSet, basename="lab-test")

urlpatterns = [
    path("reports/<int:pk>/download/", LabReportDownloadView.as_view(), name="lab-report-download"),
] + router.urls
