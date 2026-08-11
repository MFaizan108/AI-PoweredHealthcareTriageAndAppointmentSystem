from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AssistantAskView, AssistantHistoryView, HospitalFAQViewSet

router = DefaultRouter()
router.register("faqs", HospitalFAQViewSet, basename="hospital-faq")
router.register("history", AssistantHistoryView, basename="assistant-history")

urlpatterns = [
    path("ask/", AssistantAskView.as_view(), name="assistant-ask"),
] + router.urls
