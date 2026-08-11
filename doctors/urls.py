from rest_framework.routers import DefaultRouter

from .views import DoctorAvailabilityViewSet, DoctorLeaveViewSet, DoctorViewSet

router = DefaultRouter()
router.register("availability", DoctorAvailabilityViewSet, basename="doctor-availability")
router.register("leaves", DoctorLeaveViewSet, basename="doctor-leave")
router.register("", DoctorViewSet, basename="doctor")

urlpatterns = router.urls
