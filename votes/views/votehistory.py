# votes/views/history.py

from hashlib import sha256
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
        did_hash = sha256(user.did.encode()).hexdigest()  # ✅ FIX

        user_votes_qs = Vote.objects.filter(voter_did_hash=did_hash).select_related(
            "candidate", "position", "election"
        )

        candidates_qs = Candidate.objects.annotate(
            vote_count=Coalesce(Count("votes"), 0)
        )

        positions_qs = Position.objects.prefetch_related(
            Prefetch("candidates", queryset=candidates_qs)
        )

        return (
            Election.objects.filter(votes__voter_did_hash=did_hash)  # ✅ FIX
            .distinct()
            .prefetch_related(
                Prefetch("votes", queryset=user_votes_qs, to_attr="user_votes"),
                Prefetch("positions", queryset=positions_qs, to_attr="prefetched_positions"),
            )
        )
