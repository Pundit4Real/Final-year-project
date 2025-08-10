from rest_framework import serializers
from elections.models.positions import Position
from .candidates import CandidateNestedSerializer


class PositionSerializer(serializers.ModelSerializer):
    election_code = serializers.CharField(source='election.code', read_only=True)

    class Meta:
        model = Position
        fields = ['title', 'code','election', 'election_code', 'eligible_levels','eligible_departments'
                  , 'is_synced','last_synced_at'    ]
        read_only_fields = ['code'] 


class PositionNestedSerializer(serializers.ModelSerializer):
    candidates = CandidateNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Position
        fields = ['title', 'eligible_levels', 'candidates']
        read_only_fields = ['code'] 
