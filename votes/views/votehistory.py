from rest_framework import generics, permissions
from django.db.models import Prefetch, Count
from django.db.models.functions import Coalesce
from elections.models.candidates import Candidate
from elections.models.elections import Election
from elections.models.positions import Position
from votes.models import Vote
from votes.serializers.history import ElectionHistorySerializer


class VoteHistoryView(generics.ListAPIView):
    serializer_class = ElectionHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Prefetch only this user's votes
        user_votes_qs = Vote.objects.filter(voter_did_hash=user.did)

        # Prefetch candidates with vote counts already annotated
        candidates_qs = (
            # Each candidate has `vote_count`
            Candidate.objects.annotate(
                vote_count=Coalesce(Count("votes"), 0)
            )
        )

        # Prefetch positions with winner resolved in memory
        positions_qs = (
            Position.objects.prefetch_related(
                Prefetch("candidates", queryset=candidates_qs)
            )
        )

        return (
            Election.objects.filter(vote__voter_did_hash=user.did)
            .distinct()
            .select_related("school", "department")
            .prefetch_related(
                Prefetch("vote", queryset=user_votes_qs, to_attr="user_vote"),
                Prefetch("positions", queryset=positions_qs, to_attr="prefetched_positions"),
            )
        )
