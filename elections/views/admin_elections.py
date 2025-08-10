from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from elections.models.elections import Election
from elections.serializers.elections import ElectionSerializer
from elections.filters import ElectionFilter


class AdminElectionCreateView(generics.CreateAPIView):
    """
    Create a new election (Admin-only). 
    All new elections start in 'Draft' status.
    """
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        # Force status to 'draft' on creation
        serializer.save(status=Election.Status.DRAFT)


class AdminElectionListView(generics.ListAPIView):
    """
    List all elections (Admin-only) with filtering support.
    """
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ElectionFilter

    def get_queryset(self):
        return Election.objects.all()


class AdminElectionSummaryView(generics.GenericAPIView):
    """
    Return a summary of all elections (Admin-only).
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, *args, **kwargs):
        elections = Election.objects.all()
        summary = {
            "draft": elections.filter(status=Election.Status.DRAFT).count(),
            "upcoming": elections.filter(status=Election.Status.UPCOMING).count(),
            "ongoing": elections.filter(status=Election.Status.ONGOING).count(),
            "ended": elections.filter(status=Election.Status.ENDED).count(),
            "suspended": elections.filter(status=Election.Status.SUSPENDED).count(),
            "cancelled": elections.filter(status=Election.Status.CANCELLED).count(),
            "total": elections.count()
        }
        return Response(summary)
