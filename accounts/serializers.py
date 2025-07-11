from rest_framework import serializers
from datetime import datetime
from accounts.models import User,Department

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    level = serializers.IntegerField(required=False)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), required=False, write_only=True
    )
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'index_number', 'full_name', 'email', 'year_enrolled', 'level',
            'department', 'department_name', 'password'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        is_admin = request.user.is_superuser if request else False
        department = attrs.get('department')

        if not is_admin and not department:
            raise serializers.ValidationError({
                'department': 'Department is required for non-superuser account creation.'
            })

        return attrs

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
