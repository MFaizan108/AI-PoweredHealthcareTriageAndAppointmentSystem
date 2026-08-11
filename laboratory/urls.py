from rest_framework.routers import DefaultRouter

from .views import LabReportViewSet, LabTestViewSet

router = DefaultRouter()
router.register("reports", LabReportViewSet, basename="lab-report")
router.register("", LabTestViewSet, basename="lab-test")

urlpatterns = router.urls
