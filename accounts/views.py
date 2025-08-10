from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics,permissions
from rest_framework.permissions import IsAdminUser
from accounts.filters import UserFilter
from accounts.models import User
from accounts.serializers import SignupSerializer,UserListSerializer
from drf_yasg.utils import swagger_auto_schema
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi

from django.conf import settings

# ------------------------------
# 🔐 Admin-only Student Sign-Up
# ------------------------------
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
                "full_name":user.full_name,
                "did": user.did,
                "current_level": user.current_level,
                "year_enrolled": user.year_enrolled,
                "department": user.department.name if user.department else None,
                "role": user.role
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):

    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    search_fields = ['index_number','full_name','did']


class UserSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all()

        summary = {
            "active": sum(1 for u in users if u.status == "Active"),
            "suspended": sum(1 for u in users if u.status == "Suspended"),
            "inactive": sum(1 for u in users if u.status == "Inactive"),
            "total": users.count()
        }

        return Response(summary)