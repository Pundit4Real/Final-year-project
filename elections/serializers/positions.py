from rest_framework import serializers
from elections.models.positions import Position
from .candidates import CandidateNestedSerializer


class PositionSerializer(serializers.ModelSerializer):
    election_code = serializers.CharField(source='election.code', read_only=True)
    school_name = serializers.CharField(source='election.school.name', read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Position
        fields = "__all__"
        read_only_fields = ['code', 'created_at', 'is_synced']

    def validate(self, attrs):
        """
        Restrict editing once synced.
        Allow only 'description' updates if is_synced=True.
        """
        if self.instance and self.instance.is_synced:
            allowed = {"description"}
            for field in attrs.keys():
                if field not in allowed:
                    raise serializers.ValidationError(
                        {field: "This field cannot be updated after blockchain sync."}
                    )
        return attrs

class PositionNestedSerializer(serializers.ModelSerializer):
    candidates = CandidateNestedSerializer(many=True, read_only=True)
    code = serializers.CharField(read_only=True)
    school_name = serializers.CharField(source='election.school.name', read_only=True)

    class Meta:
        model = Position
        fields = ['code', 'title', 'description', 'eligible_levels', 'candidates', 'school_name']
        read_only_fields = ['code', 'title', 'eligible_levels']
