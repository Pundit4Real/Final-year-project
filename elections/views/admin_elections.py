from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from elections.models.elections import Election
from elections.serializers.elections import ElectionSerializer
from elections.filters import ElectionFilter
from blockchain.helpers import add_election


class AdminElectionCreateView(generics.CreateAPIView):
    """
    Create a new election (Admin-only).
    All new elections start in 'Draft' status and are deployed on-chain.
    """
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        # Save election with draft status
        election = serializer.save(status=Election.Status.DRAFT)

        # Deploy election on-chain
        receipt = add_election(election.code)

        # Mark as synced if transaction succeeded
        if receipt:
            election.is_synced = True
            election.save(update_fields=["is_synced"])


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
    serializer_class = ElectionSerializer


    def get(self, request, *args, **kwargs):
        elections = Election.objects.all()
        summary = {
            "draft": elections.filter(status=Election.Status.DRAFT).count(),
            "upcoming": elections.filter(status=Election.Status.UPCOMING).count(),
            "ongoing": elections.filter(status=Election.Status.ONGOING).count(),
            "ended": elections.filter(status=Election.Status.ENDED).count(),
            "postponed": elections.filter(status=Election.Status.POSTPONED).count(),
            "cancelled": elections.filter(status=Election.Status.CANCELLED).count(),
            "total": elections.count()
        }
        return Response(summary)
