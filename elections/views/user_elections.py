from django.db.models import Q, Exists, OuterRef, Count
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from elections.models.elections import Election
from elections.serializers.elections import ElectionSerializer, ElectionDetailSerializer
from votes.models import Vote


class BaseElectionView:
    """
    Mixin to ensure request is always in serializer context and queryset is optimized
    with has_voted, total_candidates, and total_positions annotations.
    """
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        voter_did_hash = getattr(user, "did_hash", None)

        vote_subquery = Vote.objects.filter(
            election=OuterRef('pk'),
            voter_did_hash=voter_did_hash
        )

        return (
            Election.objects
            .filter(Q(department__isnull=True) | Q(department=user.department))
            .annotate(
                has_voted=Exists(vote_subquery),
                total_candidates=Count('positions__candidates', distinct=True),
                total_positions=Count('positions', distinct=True)
            )
            .select_related('department')
        )


class ElectionListView(BaseElectionView, generics.ListAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated]


class ElectionSummaryView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Election.objects.filter(
            Q(department__isnull=True) | Q(department=user.department)
        )

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()

        summary = qs.aggregate(
            upcoming=Count('id', filter=Q(status=Election.Status.UPCOMING)),
            ongoing=Count('id', filter=Q(status=Election.Status.ONGOING)),
            ended=Count('id', filter=Q(status=Election.Status.ENDED)),
            suspended=Count('id', filter=Q(status=Election.Status.SUSPENDED)),
            cancelled=Count('id', filter=Q(status=Election.Status.CANCELLED)),
            total=Count('id')
        )

        return Response(summary)


class ElectionDetailView(BaseElectionView, generics.RetrieveAPIView):
    serializer_class = ElectionDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'code'

    def get_queryset(self):
        return (
            super().get_queryset()
            .prefetch_related('positions__candidates')
        )

    def retrieve(self, request, *args, **kwargs):
        election = self.get_object()
        if election.status == Election.Status.UPCOMING:
            return Response(
                {"detail": "This election has not started yet. You can only view information."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().retrieve(request, *args, **kwargs)
