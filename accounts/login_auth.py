from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers,status
from accounts.models import User
from accounts.serializers import LoginSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.response import Response

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login_serializer = LoginSerializer(data=self.initial_data)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['index_number'] = user.index_number
        token['did'] = user.did
        return token

    def validate(self, attrs):
        self.login_serializer.is_valid(raise_exception=True)
        index_number = self.login_serializer.validated_data.get("index_number")
        password = self.login_serializer.validated_data.get("password")

        try:
            user = User.objects.get(index_number=index_number)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid index number or password")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid index number or password")

        data = super().validate(attrs)
        data.update({
            "message": "Login successful",
            "index_number": user.index_number,
            "full_name":user.full_name,
            "did": user.did,
            "access": data["access"],
            "refresh": data["refresh"],
            "role": user.role
        })
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="Login with Index Number",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'index_number': openapi.Schema(type=openapi.TYPE_STRING, description='Student Index Number'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            },
            required=['index_number', 'password']
        ),
        responses={200: "JWT token pair with DID and index number"}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user  # User instance after validation

        # Blacklist all previous outstanding tokens for this user
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except Exception:
                pass  # optionally log or ignore if already blacklisted

        data = serializer.validated_data
        data.update({
            "message": "Login successful",
            "index_number": user.index_number,
            "full_name": user.full_name,
            "did": user.did,
            "role": user.role
        })

        return Response(data, status=status.HTTP_200_OK)