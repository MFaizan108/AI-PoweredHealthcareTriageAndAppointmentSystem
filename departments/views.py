from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Department
from .permissions import IsAdminOrReadOnly
from .serializers import DepartmentSerializer

LIST_CACHE_KEY = "departments:list"
LIST_CACHE_TTL = 300


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def list(self, request, *args, **kwargs):
        # Departments change rarely (admin-only writes) and are read on nearly every page — cache the
        # serialized list, then paginate the cached data so page 2+ still works correctly.
        data = cache.get(LIST_CACHE_KEY)
        if data is None:
            data = self.get_serializer(self.filter_queryset(self.get_queryset()), many=True).data
            cache.set(LIST_CACHE_KEY, data, LIST_CACHE_TTL)
        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(data)
