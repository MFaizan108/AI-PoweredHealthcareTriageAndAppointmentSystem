from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, FeedbackViewSet, WaitlistViewSet

router = DefaultRouter()
router.register("waitlist", WaitlistViewSet, basename="waitlist")
router.register("feedback", FeedbackViewSet, basename="feedback")
router.register("", AppointmentViewSet, basename="appointment")

urlpatterns = router.urls
