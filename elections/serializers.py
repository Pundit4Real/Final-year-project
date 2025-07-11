from rest_framework import serializers
from elections.models import Election, Position, Candidate


class ElectionSerializer(serializers.ModelSerializer):
    has_started = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Election
        fields = [
            'code', 'title', 'description', 'start_date', 'end_date',
            'created_at', 'has_started', 'department_name'
        ]

    def get_has_started(self, obj):
        return obj.has_started()


class PositionSerializer(serializers.ModelSerializer):
    election_code = serializers.CharField(source='election.code', read_only=True)

    class Meta:
        model = Position
        fields = ['code', 'title', 'election', 'election_code', 'eligible_levels']


class CandidateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    position_code = serializers.CharField(source='position.code', read_only=True)

    class Meta:
        model = Candidate
        fields = ['code', 'student', 'student_name', 'position', 'position_code', 'manifesto']

    def validate(self, data):
        student = data.get('student')
        position = data.get('position')

        if student.current_level == 4:
            raise serializers.ValidationError("Students in Level 400 are not eligible to contest.")

        if not position.is_user_eligible(student):
            raise serializers.ValidationError("This student is not eligible to contest for this position.")
        return data


# ✅ Nested for Election Detail
class CandidateNestedSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Candidate
        fields = ['code', 'student', 'student_name', 'manifesto']


class PositionNestedSerializer(serializers.ModelSerializer):
    candidates = CandidateNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Position
        fields = ['code', 'title', 'eligible_levels', 'candidates']


class ElectionDetailSerializer(serializers.ModelSerializer):
    positions = PositionNestedSerializer(many=True, read_only=True)
    has_started = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    has_ended = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Election
        fields = [
            'code', 'title', 'description', 'start_date', 'end_date',
            'positions', 'has_started', 'is_active', 'has_ended', 'department_name'
        ]

    def get_has_started(self, obj):
        return obj.has_started()

    def get_is_active(self, obj):
        return obj.is_active()

    def get_has_ended(self, obj):
        return obj.has_ended()
