from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MessageAttachmentDownloadView, MessageViewSet

router = DefaultRouter()
router.register("", MessageViewSet, basename="message")

urlpatterns = [
    path("<int:pk>/attachment/", MessageAttachmentDownloadView.as_view(), name="message-attachment-download"),
] + router.urls
