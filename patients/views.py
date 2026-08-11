from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Patient
from .permissions import STAFF_ROLES, IsSelfOrStaff
from .serializers import PatientSerializer


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.select_related("user")
    serializer_class = PatientSerializer
    permission_classes = [IsSelfOrStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user.is_superuser or user.role in STAFF_ROLES):
            return qs.filter(user=user)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(user__username__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__phone_number__icontains=search)
                | Q(user__email__icontains=search)
            )
        return qs

    @action(detail=False, methods=["get"])
    def me(self, request):
        patient = Patient.objects.select_related("user").get(user=request.user)
        return Response(self.get_serializer(patient).data)
