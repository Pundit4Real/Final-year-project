# votes/serializers/history.py
from rest_framework import serializers
from votes.models import Vote
from elections.models.candidates import Candidate
from elections.models.positions import Position
from elections.models.elections import Election


class CandidateHistorySerializer(serializers.ModelSerializer):
    vote_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Candidate
        fields = ["code", "student", "image", "position", "vote_count"]


class VoteHistorySerializer(serializers.ModelSerializer):
    candidate = CandidateHistorySerializer(read_only=True)

    class Meta:
        model = Vote
        fields = [
            "id",
            "receipt",
            "tx_hash",
            "status",
            "block_number",
            "block_confirmations",
            "block_timestamp",
            "created_at",
            "candidate",
        ]


class PositionHistorySerializer(serializers.ModelSerializer):
    candidates = CandidateHistorySerializer(many=True, read_only=True)
    user_vote = serializers.SerializerMethodField()
    winner = serializers.SerializerMethodField()

    class Meta:
        model = Position
        fields = ["code", "title", "description", "candidates", "user_vote", "winner"]

    def get_user_vote(self, obj):
        """Return this user's vote for this position (if any)."""
        user_votes = self.context.get("user_votes", {})
        vote = user_votes.get(obj.id)
        return VoteHistorySerializer(vote, context=self.context).data if vote else None

    def get_winner(self, obj):
        """Pick candidate with the most votes (vote_count annotated already)."""
        candidates = list(obj.candidates.all())
        if not candidates:
            return None
        winner = max(candidates, key=lambda c: getattr(c, "vote_count", 0))
        return CandidateHistorySerializer(winner, context=self.context).data


class ElectionHistorySerializer(serializers.ModelSerializer):
    positions = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = [
            "code",
            "title",
            "description",
            "start_date",
            "end_date",
            "positions",
        ]

    def get_positions(self, obj):
        """Inject this election’s user_votes map for Position serializer."""
        user_votes = getattr(obj, "user_votes", [])
        user_votes_map = {vote.position_id: vote for vote in user_votes}

        return PositionHistorySerializer(
            getattr(obj, "prefetched_positions", obj.positions.all()),
            many=True,
            context={**self.context, "user_votes": user_votes_map},
        ).data
