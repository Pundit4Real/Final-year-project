from blockchain.helpers import get_results
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
        operation_summary="Get vote results for a specific election and position",
        manual_parameters=[
            openapi.Parameter("election_code", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter("position_code", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
        ]
    )
    def get(self, request):
        election_code = request.GET.get("election_code")
        position_code = request.GET.get("position_code")

        if not election_code or not position_code:
            return Response({"error": "election_code and position_code are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            election = Election.objects.get(code=election_code)
            position = Position.objects.get(code=position_code, election=election)
        except (Election.DoesNotExist, Position.DoesNotExist):
            return Response({"error": "Election or Position not found."}, status=status.HTTP_404_NOT_FOUND)

        total_votes_cast = Vote.objects.filter(election=election).count()
        total_votes_synced = Vote.objects.filter(election=election, is_synced=True).count()
        percent_synced = (total_votes_synced / total_votes_cast * 100) if total_votes_cast else 0

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
            vote_count = v['total_votes']
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
            res['is_winner'] = res['candidate_code'] in winners

        return Response({
            "election": election.title,
            "position": position.title,
            "total_votes_cast": total_votes_cast,
            "total_votes_synced": total_votes_synced,
            "percent_synced": round(percent_synced, 2),
            "total_votes_position": total_votes_position,
            "results": results,
        })


class BlockchainResultsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, position_code):
        codes, counts = get_results(position_code)
        return Response({
            "position_code": position_code,
            "results": [
                {"candidate_code": code, "votes": count}
                for code, count in zip(codes, counts)
            ]
        })
