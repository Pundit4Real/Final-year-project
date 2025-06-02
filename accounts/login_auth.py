from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from accounts.models import User
from accounts.serializers import LoginSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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
            "did": user.did,
            "access": data["access"],
            "refresh": data["refresh"]
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
        return super().post(request, *args, **kwargs)
