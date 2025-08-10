from blockchain.helpers import get_results
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from votes.models import Vote
from elections.models.elections import Election
from elections.models.positions import Position
from votes.serializers import AnonymousVoteSerializer
from django.db.models import Count


class CastVoteView(generics.CreateAPIView):
    serializer_class = AnonymousVoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Cast a vote",
        operation_description="Vote anonymously using election, position, and candidate codes.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "election_code": openapi.Schema(type=openapi.TYPE_STRING),
                "position_code": openapi.Schema(type=openapi.TYPE_STRING),
                "candidate_code": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["election_code", "position_code", "candidate_code"]
        ),
        responses={201: "Vote cast successfully", 400: "Invalid input or already voted."}
    )
    def post(self, request, *args, **kwargs):
        election_code = request.data.get("election_code")
        position_code = request.data.get("position_code")
        candidate_code = request.data.get("candidate_code")

        if not all([election_code, position_code, candidate_code]):
            return Response({"error": "All codes are required."}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "election_code": election_code,
            "position_code": position_code,
            "candidate_code": candidate_code
        }

        serializer = self.get_serializer(data=data, context={"request": request})
        if serializer.is_valid():
            vote_instance = serializer.save()
            return Response({
                "message": "Vote cast successfully.",
                "receipt": vote_instance.receipt,
                "tx_mined_hash": vote_instance.tx_hash,
                "timestamp": vote_instance.timestamp,
                "position": vote_instance.position.title,
                "election": vote_instance.election.title,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoteVerificationView(APIView):
    @swagger_auto_schema(
        operation_summary="Verify a vote",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "receipt": openapi.Schema(type=openapi.TYPE_STRING, description="Unique receipt issued after vote"),
            },
            required=["receipt"]
        )
    )
    def post(self, request):
        receipt = request.data.get('receipt')
        if not receipt:
            return Response({"error": "Receipt is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vote = Vote.objects.select_related('candidate', 'position', 'election').get(receipt=receipt)
        except Vote.DoesNotExist:
            return Response({"valid": False, "message": "No vote found for this receipt."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "valid": True,
            "election": vote.election.title,
            "position": vote.position.title,
            "candidate": vote.candidate.student.full_name,
            "timestamp": vote.timestamp,
        })


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

        result_data = (
            Vote.objects.filter(election=election, position=position)
            .values("candidate__student__full_name", "candidate__code")
            .annotate(total_votes=Count("id"))
            .order_by("-total_votes")
        )

        return Response({
            "election": election.title,
            "position": position.title,
            "results": result_data
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
