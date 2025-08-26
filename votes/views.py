from blockchain.helpers import get_results, get_ballot_results
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
from web3.exceptions import ContractLogicError
import logging


logger = logging.getLogger(__name__)
class CastVoteView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """
        Dynamically choose serializer:
        - If request includes 'votes' (list), use BallotVoteSerializer (voteBatch).
        - Otherwise, use AnonymousVoteSerializer (single vote).
        """
        if isinstance(self.request.data.get("votes"), list):
            from votes.serializers import BallotVoteSerializer
            return BallotVoteSerializer
        return AnonymousVoteSerializer

    def perform_create(self, serializer):
        """
        Always bind voter_did from the authenticated user.
        Prevents clients from spoofing voter identity.
        """
        voter_did_hash = getattr(self.request.user, "did", None)
        if not voter_did_hash:
            raise ValueError("Authenticated user has no DID set.")
        serializer.save(voter_did=voter_did_hash)

    @swagger_auto_schema(
        operation_summary="Cast a vote or ballot",
        operation_description="Supports both single vote and multi-position ballot voting.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Submit either a single vote or a ballot",
            properties={
                "election_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Election code",
                    example="ELECTION2025"
                ),
                "position_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Position code (for single vote)",
                    example="PRESIDENT"
                ),
                "candidate_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Candidate code (for single vote)",
                    example="CAND123"
                ),
                "votes": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="List of votes for ballot",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "position_code": openapi.Schema(
                                type=openapi.TYPE_STRING, example="PRESIDENT"
                            ),
                            "candidate_code": openapi.Schema(
                                type=openapi.TYPE_STRING, example="CAND123"
                            ),
                        },
                        required=["position_code", "candidate_code"]
                    )
                )
            },
            required=["election_code"]
        ),
        responses={
            201: "Vote(s) cast successfully",
            400: "Invalid input or already voted",
            500: "Unexpected server error"
        },
    )
    def post(self, request, *args, **kwargs):
        logger.debug("Incoming vote request: %s", request.data)

        serializer = self.get_serializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            try:
                logger.debug("Serializer validated data: %s", serializer.validated_data)

                # save() now forces voter_did=request.user.did via perform_create
                result = self.perform_create(serializer)
                logger.debug("Serializer save() returned: %s", result)

                # Ballot vote (list of votes)
                if isinstance(result, list):
                    logger.debug("Ballot vote detected, votes=%s", len(result))
                    return Response({
                        "message": "Ballot cast successfully.",
                        "tx_hash": result[0].tx_hash if result else None,
                        "votes": [
                            {
                                "receipt": v.receipt,
                                "position": v.position.title,
                                "candidate": v.candidate.student.full_name,
                                "status": v.status,
                            }
                            for v in result
                        ]
                    }, status=status.HTTP_201_CREATED)

                # Single vote
                vote_instance = result
                blockchain_info = getattr(vote_instance, "blockchain_info", {})

                logger.debug("Single vote instance blockchain info: %s", blockchain_info)

                return Response({
                    "message": "Vote cast successfully.",
                    "receipt": vote_instance.receipt,
                    "tx_hash": vote_instance.tx_hash,
                    "status": blockchain_info.get("status", "Unknown"),
                    "block_number": blockchain_info.get("block_number"),
                    "block_confirmations": blockchain_info.get("block_confirmations"),
                    "block_timestamp": blockchain_info.get("block_timestamp"),
                    "position": vote_instance.position.title,
                    "election": vote_instance.election.title,
                }, status=status.HTTP_201_CREATED)

            except ContractLogicError as e:
                logger.error("ContractLogicError: %s", e, exc_info=True)
                if "Receipt already used" in str(e):
                    return Response({
                        "error": "Previous receipt was already used. Please retry to generate a fresh receipt."
                    }, status=status.HTTP_400_BAD_REQUEST)
                return Response(
                    {"error": "Blockchain rejected the vote due to contract logic error."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                logger.error("Unexpected error during vote casting: %s", e, exc_info=True)
                return Response(
                    {"error": "An unexpected error occurred during vote casting. Please retry."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        logger.warning("Serializer validation errors: %s", serializer.errors)
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

class BlockchainBallotResultsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get blockchain results for all positions in an election",
        manual_parameters=[
            openapi.Parameter("election_code", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
        ]
    )
    def get(self, request):
        election_code = request.GET.get("election_code")
        if not election_code:
            return Response({"error": "election_code is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            raw_results = get_ballot_results(election_code)

            # Group results by position_code
            grouped = {}
            for r in raw_results:
                pos = r["position_code"]
                cand = {
                    "candidate_code": r["candidate_code"],
                    "votes": r["votes"],
                }
                grouped.setdefault(pos, []).append(cand)

            # Find winners per position
            positions = []
            for pos_code, candidates in grouped.items():
                max_votes = max([c["votes"] for c in candidates]) if candidates else 0
                for c in candidates:
                    c["is_winner"] = c["votes"] == max_votes and max_votes > 0
                positions.append({
                    "position_code": pos_code,
                    "candidates": candidates
                })

            return Response({
                "election_code": election_code,
                "positions": positions
            })

        except Exception as e:
            logger.exception(f"Error fetching blockchain ballot results: {e}")
            return Response({"error": "Failed to fetch blockchain results."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
