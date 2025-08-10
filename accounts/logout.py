from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Logout (Blacklist all tokens for user)",
        responses={
            205: "Successfully logged out from all sessions.",
            400: "Invalid request"
        }
    )
    def post(self, request):
        user = request.user

        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception as e:
            return Response(
                {"error": f"Failed to blacklist tokens: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Successfully logged out from all sessions."},
            status=status.HTTP_205_RESET_CONTENT
        )
