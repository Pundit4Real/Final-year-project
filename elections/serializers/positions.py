from rest_framework import serializers
from elections.models.positions import Position
from .candidates import CandidateNestedSerializer


class PositionSerializer(serializers.ModelSerializer):
    election_code = serializers.CharField(source='election.code', read_only=True)
    school_name = serializers.CharField(source='election.school.name', read_only=True)

    class Meta:
        model = Position
        fields = "__all__"
        read_only_fields = ['code']


class PositionNestedSerializer(serializers.ModelSerializer):
    candidates = CandidateNestedSerializer(many=True, read_only=True)
    code = serializers.CharField(read_only=True)
    school_name = serializers.CharField(source='election.school.name', read_only=True)

    class Meta:
        model = Position
        fields = ['code', 'title', 'eligible_levels', 'candidates', 'school_name']
        read_only_fields = ['code']
