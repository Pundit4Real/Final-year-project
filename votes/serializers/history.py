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
        """
        Return only the current user's vote for this position.
        Uses prefetched user_votes passed from ElectionHistorySerializer.
        """
        user_votes = self.context.get("user_votes", {})
        vote = user_votes.get(obj.id)
        return VoteHistorySerializer(vote, context=self.context).data if vote else None

    def get_winner(self, obj):
        """
        Return the candidate with the most votes for this position.
        Winner is resolved in-memory from annotated vote_count (no queries).
        """
        if not hasattr(obj, "candidates"):
            return None
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
        """
        Pass prefetched user_votes down to positions serializer,
        so no fallback queries are needed.
        """
        user_votes = getattr(obj, "user_votes", [])
        # Build dict {position_id: vote} for fast lookup
        user_votes_map = {vote.position_id: vote for vote in user_votes}

        return PositionHistorySerializer(
            obj.prefetched_positions if hasattr(obj, "prefetched_positions") else obj.positions.all(),
            many=True,
            context={**self.context, "user_votes": user_votes_map},
        ).data
