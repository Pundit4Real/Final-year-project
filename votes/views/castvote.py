import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from votes.serializers.votes import AnonymousVoteSerializer
from web3.exceptions import ContractLogicError

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
            from votes.serializers.batchvote import BallotVoteSerializer
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
        return serializer.save(voter_did=voter_did_hash)

    @swagger_auto_schema(
        operation_summary="Cast a vote or ballot",
        operation_description="Supports both single vote and multi-position ballot voting.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Submit either a single vote or a ballot",
            properties={
                "election_code": openapi.Schema(type=openapi.TYPE_STRING, example="ELECTION2025"),
                "position_code": openapi.Schema(type=openapi.TYPE_STRING, example="PRESIDENT"),
                "candidate_code": openapi.Schema(type=openapi.TYPE_STRING, example="CAND123"),
                "votes": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="List of votes for ballot",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "position_code": openapi.Schema(type=openapi.TYPE_STRING, example="PRESIDENT"),
                            "candidate_code": openapi.Schema(type=openapi.TYPE_STRING, example="CAND123"),
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

                result = self.perform_create(serializer)
                logger.debug("Serializer save() returned: %s", result)

                # Ballot vote (list of votes)
                if isinstance(result, list):
                    logger.debug("Ballot vote detected, votes=%s", len(result))
                    return Response({
                        "message": "Ballot cast successfully.",
                        "tx_hash": getattr(result[0], "tx_hash", None) if result else None,
                        "votes": [
                            {
                                "receipt": getattr(v, "receipt", None),
                                "position": getattr(v.position, "title", None),
                                "candidate": getattr(v.candidate.student, "full_name", None),
                                "status": getattr(v, "status", "Unknown"),
                            }
                            for v in result
                        ]
                    }, status=status.HTTP_201_CREATED)

                # Single vote
                vote_instance = result
                blockchain_info = getattr(vote_instance, "blockchain_info", {}) or {}

                logger.debug("Single vote instance blockchain info: %s", blockchain_info)

                return Response({
                    "message": "Vote cast successfully.",
                    "receipt": getattr(vote_instance, "receipt", None),
                    "tx_hash": getattr(vote_instance, "tx_hash", None),
                    "status": blockchain_info.get("status", "Unknown"),
                    "block_number": blockchain_info.get("block_number"),
                    "block_confirmations": blockchain_info.get("block_confirmations"),
                    "block_timestamp": blockchain_info.get("block_timestamp"),
                    "position": getattr(vote_instance.position, "title", None),
                    "election": getattr(vote_instance.election, "title", None),
                }, status=status.HTTP_201_CREATED)

            except ContractLogicError as e:
                logger.error("ContractLogicError: %s", e, exc_info=True)
                if "Receipt already used" in str(e):
                    return Response(
                        {"error": "Previous receipt was already used. Please retry to generate a fresh receipt."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
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
