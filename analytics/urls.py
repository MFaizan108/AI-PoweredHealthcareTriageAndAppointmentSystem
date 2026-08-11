from django.urls import path

from .views import AIAnalyticsView, AppointmentAnalyticsView, PatientAnalyticsView

urlpatterns = [
    path("patients/", PatientAnalyticsView.as_view(), name="analytics-patients"),
    path("appointments/", AppointmentAnalyticsView.as_view(), name="analytics-appointments"),
    path("ai/", AIAnalyticsView.as_view(), name="analytics-ai"),
]
