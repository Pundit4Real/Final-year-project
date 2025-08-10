from rest_framework import serializers
from elections.models.candidates import Candidate


class CandidateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    position_code = serializers.CharField(source='position.code', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    election_title = serializers.CharField(source='position.election.title', read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            'code',
            'student',
            'student_name',
            'position',
            'position_code',
            'position_title',
            'election_title',
            'manifesto',
            'image',
            'campaign_keywords',
            'promise'
        ]
        read_only_fields = [
            'code',
            'student_name',
            'position_code',
            'position_title',
            'election_title'
        ]

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def validate(self, data):
        student = data.get('student')
        position = data.get('position')

        if student.current_level == 4:
            raise serializers.ValidationError(
                "Students in Level 400 are not eligible to contest."
            )

        if not position.is_user_eligible(student):
            raise serializers.ValidationError(
                "This student is not eligible to contest for this position."
            )
        return data


class CandidateNestedSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Candidate
        fields = "__all__"
        read_only_fields = ['code']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None
