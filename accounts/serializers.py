from rest_framework import serializers
from datetime import datetime
from .models import User

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    level = serializers.IntegerField(required=False)

    class Meta:
        model = User
        fields = ['index_number', 'full_name', 'email', 'year_enrolled', 'level', 'password']


    def create(self, validated_data):
        level = validated_data.get('level')
        year_enrolled = validated_data.get('year_enrolled')

        if not year_enrolled and level:
            current_year = datetime.now().year
            validated_data['year_enrolled'] = current_year - (level - 1)

        return User.objects.create_user(**validated_data)



class LoginSerializer(serializers.Serializer):
    index_number = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
