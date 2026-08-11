from rest_framework.routers import DefaultRouter

from .views import DiagnosisViewSet, MedicalRecordViewSet

router = DefaultRouter()
router.register("diagnoses", DiagnosisViewSet, basename="diagnosis")
router.register("", MedicalRecordViewSet, basename="medical-record")

urlpatterns = router.urls
