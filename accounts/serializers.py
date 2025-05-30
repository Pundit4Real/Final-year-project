from rest_framework import serializers
from .models import User

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['index_number', 'full_name', 'email', 'year_enrolled', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)