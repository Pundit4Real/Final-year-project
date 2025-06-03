from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Election
from .serializers import ElectionSerializer, ElectionDetailSerializer
from datetime import datetime
from django.db.models import Q


class ElectionListView(generics.ListAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Election.objects.filter(
            Q(department__isnull=True) | Q(department=user.department)
        )


class ElectionDetailView(generics.RetrieveAPIView):
    serializer_class = ElectionDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Election.objects.filter(
            Q(department__isnull=True) | Q(department=user.department)
        ).prefetch_related('positions__candidates')

    def retrieve(self, request, *args, **kwargs):
        election = self.get_object()
        if not election.has_started():
            return Response(
                {"detail": "This election has not started yet. You can only view information."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().retrieve(request, *args, **kwargs)
