from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/accounts/', include('accounts.urls')),
    path('api/departments/', include('departments.urls')),
    path('api/patients/', include('patients.urls')),
    path('api/doctors/', include('doctors.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/medical-records/', include('medical_records.urls')),
    path('api/prescriptions/', include('prescriptions.urls')),
    path('api/lab/', include('laboratory.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/triage/', include('triage.urls')),
    path('api/audit-logs/', include('audit_logs.urls')),
    path('api/billing/', include('billing.urls')),
    path('api/messages/', include('messaging.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/ai-assistant/', include('ai_assistant.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
