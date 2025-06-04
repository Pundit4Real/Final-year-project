from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from votes.models import Vote
from votes.serializers import AnonymousVoteSerializer


class CastVoteView(generics.CreateAPIView):
    serializer_class = AnonymousVoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Cast a vote",
        operation_description="Allows an authenticated student to vote anonymously. Returns a receipt for verification.",
        responses={
            201: openapi.Response(
                description="Vote cast successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "receipt": openapi.Schema(type=openapi.TYPE_STRING),
                        "timestamp": openapi.Schema(type=openapi.FORMAT_DATETIME),
                        "position": openapi.Schema(type=openapi.TYPE_STRING),
                        "election": openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Invalid input or already voted."
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            vote_instance = serializer.save()
            return Response({
                "message": "Vote cast successfully.",
                "receipt": vote_instance.receipt,
                "timestamp": vote_instance.timestamp,
                "position": vote_instance.position.title,
                "election": vote_instance.election.title,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoteVerificationView(APIView):
    @swagger_auto_schema(
        operation_summary="Verify a vote",
        operation_description="Accepts a receipt and returns the vote details if valid.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "receipt": openapi.Schema(type=openapi.TYPE_STRING, description="Unique receipt issued after vote"),
            },
            required=["receipt"]
        ),
        responses={
            200: openapi.Response(
                description="Verification success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "valid": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "election": openapi.Schema(type=openapi.TYPE_STRING),
                        "position": openapi.Schema(type=openapi.TYPE_STRING),
                        "candidate": openapi.Schema(type=openapi.TYPE_STRING),
                        "timestamp": openapi.Schema(type=openapi.FORMAT_DATETIME),
                    }
                )
            ),
            404: "No vote found for this receipt."
        }
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
