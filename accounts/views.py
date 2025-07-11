from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser

from accounts.serializers import SignupSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class SignupView(APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'index_number': openapi.Schema(type=openapi.TYPE_STRING, description='Student Index Number'),
                'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Student Full Name'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Student Email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'level': openapi.Schema(type=openapi.TYPE_INTEGER, description='Optional current level (1–4)'),
                'year_enrolled': openapi.Schema(type=openapi.TYPE_INTEGER, description='Optional year student enrolled'),
                'department': openapi.Schema(type=openapi.TYPE_INTEGER, description='Department ID'),
            },
            required=['index_number', 'full_name', 'email', 'password']
        )
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Student account created successfully.",
                "index_number": user.index_number,
                "did": user.did,
                "current_level": user.current_level,
                "year_enrolled": user.year_enrolled,
                "department": user.department.name if user.department else None
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




from django.core.management import call_command
from django.http import HttpResponse

def setup_view(request):
    call_command('migrate')
    call_command('loaddata', 'data.json')
    return HttpResponse("✔ Database migrated and data loaded.")
