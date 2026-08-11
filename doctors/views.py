from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import User

from .models import Doctor, DoctorAvailability, DoctorLeave
from .permissions import IsAdminOrOwnerDoctorOrReadOnly
from .serializers import DoctorAvailabilitySerializer, DoctorLeaveSerializer, DoctorSerializer


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.select_related("user", "department").filter(is_active=True)
    serializer_class = DoctorSerializer
    permission_classes = [IsAdminOrOwnerDoctorOrReadOnly]

    def get_queryset(self):
        qs = Doctor.objects.select_related("user", "department")
        user = self.request.user
        if not (user.is_authenticated and (user.is_superuser or user.role == User.Role.ADMIN)):
            qs = qs.filter(is_active=True)
        department = self.request.query_params.get("department")
        if department:
            qs = qs.filter(department_id=department)
        return qs


class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = DoctorAvailability.objects.select_related("doctor")
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnerDoctorOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        doctor = self.request.query_params.get("doctor")
        if doctor:
            qs = qs.filter(doctor_id=doctor)
        return qs


class DoctorLeaveViewSet(viewsets.ModelViewSet):
    queryset = DoctorLeave.objects.select_related("doctor")
    serializer_class = DoctorLeaveSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnerDoctorOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        doctor = self.request.query_params.get("doctor")
        if doctor:
            qs = qs.filter(doctor_id=doctor)
        return qs
