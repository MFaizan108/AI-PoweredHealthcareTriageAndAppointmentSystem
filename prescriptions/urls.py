from rest_framework.routers import DefaultRouter

from .views import PrescriptionItemViewSet, PrescriptionViewSet

router = DefaultRouter()
router.register("items", PrescriptionItemViewSet, basename="prescription-item")
router.register("", PrescriptionViewSet, basename="prescription")

urlpatterns = router.urls
