from rest_framework import serializers
from elections.models import Election, Position, Candidate
from accounts.models import User


class ElectionSerializer(serializers.ModelSerializer):
    has_started = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'created_at', 'has_started']

    def get_has_started(self, obj):
        return obj.has_started()


class PositionSerializer(serializers.ModelSerializer):
    election_title = serializers.CharField(source='election.title', read_only=True)

    class Meta:
        model = Position
        fields = ['id', 'title', 'election', 'election_title', 'eligible_levels']


class CandidateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)

    class Meta:
        model = Candidate
        fields = ['id', 'student', 'student_name', 'position', 'position_title', 'manifesto']


# =====================
# ✅ Nested Serializers
# =====================

class CandidateNestedSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Candidate
        fields = ['id', 'student', 'student_name', 'manifesto']


class PositionNestedSerializer(serializers.ModelSerializer):
    candidates = CandidateNestedSerializer(many=True, source='candidates', read_only=True)

    class Meta:
        model = Position
        fields = ['id', 'title', 'eligible_levels', 'candidates']


class ElectionDetailSerializer(serializers.ModelSerializer):
    positions = PositionNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'positions']
