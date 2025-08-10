from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from elections.models.elections import Election
from elections.serializers.elections import ElectionSerializer, ElectionDetailSerializer


class ElectionListView(generics.ListAPIView):
    """
    List elections available to the authenticated user.
    University-wide elections are included, along with elections
    specific to the user's department.
    """
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Election.objects.filter(
            Q(department__isnull=True) | Q(department=user.department)
        )


class ElectionSummaryView(generics.GenericAPIView):
    """
    Return a summary of elections available to the user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        elections = self.get_queryset()
        summary = {
            "upcoming": sum(1 for e in elections if e.get_status().lower() == "upcoming"),
            "ongoing": sum(1 for e in elections if e.get_status().lower() == "ongoing"),
            "ended": sum(1 for e in elections if e.get_status().lower() == "ended"),
            "suspended": sum(1 for e in elections if e.get_status().lower() == "suspended"),
            "cancelled": sum(1 for e in elections if e.get_status().lower() == "cancelled"),
            "total": elections.count()
        }
        return Response(summary)

    def get_queryset(self):
        user = self.request.user
        return Election.objects.filter(
            Q(department__isnull=True) | Q(department=user.department)
        )


class ElectionDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of an election if it has started.
    Restricts elections to those available to the user.
    """
    serializer_class = ElectionDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'code'

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
