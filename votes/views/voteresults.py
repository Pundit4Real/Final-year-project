from blockchain.helpers import get_results,get_ballot_results
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from votes.models import Vote
from elections.models.elections import Election
from elections.models.positions import Position
from django.db.models import Count


class VoteResultsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get vote results for an election (all positions) or a specific position",
        manual_parameters=[
            openapi.Parameter("election_code", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter("position_code", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
        ]
    )
    def get(self, request):
        election_code = request.GET.get("election_code")
        position_code = request.GET.get("position_code")

        if not election_code:
            return Response({"error": "election_code is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            election = Election.objects.get(code=election_code)
        except Election.DoesNotExist:
            return Response({"error": "Election not found."}, status=status.HTTP_404_NOT_FOUND)

        total_votes_cast = Vote.objects.filter(election=election).count()
        total_votes_synced = Vote.objects.filter(election=election, is_synced=True).count()
        percent_synced = (total_votes_synced / total_votes_cast * 100) if total_votes_cast else 0

        # If a single position_code is provided → return results for that position only
        if position_code:
            try:
                position = Position.objects.get(code=position_code, election=election)
            except Position.DoesNotExist:
                return Response({"error": "Position not found in this election."}, status=status.HTTP_404_NOT_FOUND)

            position_results = self._calculate_position_results(election, position)
            return Response({
                "election": election.title,
                "position": position.title,
                "total_votes_cast": total_votes_cast,
                "total_votes_synced": total_votes_synced,
                "percent_synced": round(percent_synced, 2),
                **position_results
            })

        # Otherwise → return results for ALL positions in this election
        all_positions = Position.objects.filter(election=election)
        election_results = []
        for pos in all_positions:
            pos_result = self._calculate_position_results(election, pos)
            election_results.append({
                "position": pos.title,
                **pos_result
            })

        return Response({
            "election": election.title,
            "total_votes_cast": total_votes_cast,
            "total_votes_synced": total_votes_synced,
            "percent_synced": round(percent_synced, 2),
            "positions": election_results,
        })

    def _calculate_position_results(self, election, position):
        """Helper to compute results for a single position."""
        total_votes_position = Vote.objects.filter(position=position).count()

        votes_qs = (
            Vote.objects.filter(election=election, position=position)
            .values("candidate__student__full_name", "candidate__code")
            .annotate(total_votes=Count("id"))
            .order_by("-total_votes")
        )

        results = []
        max_votes = 0
        winners = []

        for v in votes_qs:
            vote_count = v["total_votes"]
            percent = (vote_count / total_votes_position * 100) if total_votes_position else 0
            results.append({
                "candidate_full_name": v["candidate__student__full_name"],
                "candidate_code": v["candidate__code"],
                "total_votes": vote_count,
                "percentage": round(percent, 2),
            })
            if vote_count > max_votes:
                max_votes = vote_count
                winners = [v["candidate__code"]]
            elif vote_count == max_votes:
                winners.append(v["candidate__code"])

        for res in results:
            res["is_winner"] = res["candidate_code"] in winners

        return {
            "total_votes_position": total_votes_position,
            "results": results,
        }

class BlockchainResultsView(APIView):
    """
    Fetch results from blockchain.
    Supports:
      - position_code: single position results
      - election_code: all positions under election
    """

    def get(self, request, *args, **kwargs):
        position_code = request.query_params.get("position_code")
        election_code = request.query_params.get("election_code")

        # Case 1: Single position results
        if position_code:
            try:
                position = Position.objects.get(code=position_code)
                results = get_ballot_results(position.code)
                return Response({
                    "election": position.election.name,
                    "position": position.name,
                    "results": results
                }, status=status.HTTP_200_OK)
            except Position.DoesNotExist:
                return Response({"error": "Position not found"}, status=status.HTTP_404_NOT_FOUND)

        # Case 2: Whole election results
        elif election_code:
            try:
                election = Election.objects.get(code=election_code)
                election_results = []

                for position in election.positions.all():
                    results = get_ballot_results(position.code)
                    election_results.append({
                        "position": position.name,
                        "results": results
                    })

                return Response({
                    "election": election.name,
                    "positions": election_results
                }, status=status.HTTP_200_OK)
            except Election.DoesNotExist:
                return Response({"error": "Election not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"error": "Provide either position_code or election_code"},
            status=status.HTTP_400_BAD_REQUEST
        )