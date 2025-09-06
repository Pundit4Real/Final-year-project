from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import  status
from rest_framework.views import APIView
from rest_framework.response import Response
from votes.models import Vote
from votes.models import Vote

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
            "timestamp": vote.block_timestamp,
            "tx_hash": vote.tx_hash,
            "receipt_hash": vote.receipt,
            "block_number": vote.block_number,
            "confirmations": vote.block_confirmations,
        })

